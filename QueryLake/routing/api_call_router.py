from fastapi import UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, Response, JSONResponse
import asyncio
import json
import inspect
import logging
import traceback

from QueryLake.runtime.db_compat import QueryLakeUnsupportedFeatureError, QueryLakeProfileConfigurationError

logger = logging.getLogger(__name__)

async def api_general_call(
    self, # Umbrella class, can't type hint because of circular imports
    clean_function_arguments_for_api,
    API_FUNCTION_HELP_DICTIONARY,
    API_FUNCTION_HELP_GUIDE, 
    req: Request, 
    rest_of_path: str, 
    file: UploadFile = None
):
    """
    This is a wrapper around every api function that is allowed. 
    It will call the function with the arguments provided, after filtering them for security.
    """
    
    try:
        logger.info("Routing API call to %s", rest_of_path)

        if not file is None:
            logger.debug("Attached file for API call: %s", file.filename)
        
        if "parameters" in req.query_params._dict:
            arguments = json.loads(req.query_params._dict["parameters"])
        else:
            body_bytes = await asyncio.wait_for(req.body(), timeout=10)
            if not body_bytes:
                arguments = {}
            else:
                try:
                    arguments = json.loads(body_bytes)
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                    logger.debug("Non-JSON body for %s; treating as empty arguments", rest_of_path)
                    arguments = {}
        
        # print("arguments:", arguments)
        route = req.scope['path']
        route_split = route.split("/")
        logger.debug("API route prefix: %s", "/".join(route_split[:3]))
        if rest_of_path == "help":
            if len(route_split) > 3:
                function_name = route_split[3]
                return {"success": True, "note": API_FUNCTION_HELP_DICTIONARY[function_name]}
            else:
                logger.debug("API help guide requested")
                return {"success": True, "note": API_FUNCTION_HELP_GUIDE}
        else:
            function_actual = self.api_function_getter(rest_of_path.split("/")[0])
            true_args = clean_function_arguments_for_api(
                self.default_function_arguments, 
                arguments, 
                function_object=function_actual
            )
            
            if inspect.iscoroutinefunction(function_actual):
                args_get = await function_actual(**true_args)
            else:
                args_get = function_actual(**true_args)
            
            # print("Type of args_get:", type(args_get))
            
            if type(args_get) is StreamingResponse:
                return args_get
            elif type(args_get) is FileResponse:
                return args_get
            elif type(args_get) is Response:
                return args_get
            elif args_get is True:
                return {"success": True}
            return {"success": True, "result": args_get}
    except (QueryLakeUnsupportedFeatureError, QueryLakeProfileConfigurationError) as e:
        self.database.rollback()
        self.database.flush()
        logger.warning("Capability/profile error on %s: %s", rest_of_path, str(e))
        status_code = 501 if isinstance(e, QueryLakeUnsupportedFeatureError) else 500
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": str(e),
                "detail": e.to_payload(),
            },
        )
    except HTTPException as e:
        self.database.rollback()
        self.database.flush()
        detail = e.detail
        if isinstance(detail, dict):
            message = detail.get("message") or detail.get("error") or str(detail)
        else:
            message = str(detail)
        logger.warning("HTTP error on %s: %s", rest_of_path, message)
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error": message,
                "detail": detail,
            },
        )
    except AssertionError as e:
        self.database.rollback()
        self.database.flush()
        detail = {
            "type": "invalid_request",
            "code": "ql.invalid_request",
            "message": str(e) or "Invalid request",
            "docs_ref": "docs/sdk/API_REFERENCE.md",
            "retryable": False,
        }
        logger.warning("Assertion error on %s: %s", rest_of_path, detail["message"])
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": detail["message"],
                "detail": detail,
            },
        )
    except Exception as e:
        self.database.rollback()
        self.database.flush()
        error_message = str(e)
        stack_trace = traceback.format_exc()
        logger.exception("API call to %s failed: %s", rest_of_path, error_message)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": error_message, "trace": stack_trace},
        )
