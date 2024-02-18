import { Dispatch } from "react";
import { compositionObjectType, compositionType, substituteAny } from "@/typing/toolchains";
import { SERVER_ADDR_WS } from "@/config_server_hostnames";
// import { stat } from "fs";
// import { get } from "http";

type stateSet = Dispatch<React.SetStateAction<Map<string, substituteAny>>> | ((new_state : Map<string, substituteAny>) => void)
type titleSet = Dispatch<React.SetStateAction<string>> | ((new_state : string) => void)

export default class ToolchainSession {
    private onStateChange: stateSet;
    private onTitleChange: titleSet;
    private socket: WebSocket; // Add socket as a type
    private state: Map<string, substituteAny>;
    private stream_mappings: { [key: string]: (string | number)[][] };

    constructor ( onStateChange: stateSet, 
                  onTitleChange: titleSet ) {
        this.onStateChange = onStateChange;
        this.onTitleChange = onTitleChange;
        this.socket = new WebSocket(`${SERVER_ADDR_WS}/toolchain`);
        
        this.state = new Map<string, substituteAny>();
        this.stream_mappings = {} as { [key : string ] : (string | number)[][]};

        this.socket.onmessage = async (event: MessageEvent) => {
            try {
                const message_text : Blob = event.data;
                const message_text_string : string = await message_text.text();
                const message = JSON.parse(message_text_string);
                this.handle_message(message);
            } catch (error) {
                console.error("Error parsing message:", error);
            }
        };

        this.socket.onopen = () => {
            console.log("Connected to server");
        }
    }

    handle_message(data : { [key : string] : substituteAny }) {
        // if ("ACTION" in parsedResponse && parsedResponse["ACTION"] === "END_WS_CALL") {
        //     break;
        // } else {
        //     final_output = parsedResponse;
        // }

        if ("trace" in data) {
            console.log(data);
        } else if ("state" in data) {
            this.state = data["state"] as Map<string, substituteAny>;
        } else if ("type" in data) {

            

            if (data["type"] === "streaming_output_mapping") {
                const data_typed = data as {"type" : "streaming_output_mapping", "stream_id" : string, "routes" : (string | number)[][]};

                this.stream_mappings[data_typed["stream_id"]] = data_typed["routes"];
            } else if (data["type"] === "state_diff") {
                const data_typed = data as {
                    "type" : "state_diff", 
                    "stream_id" : string, 
                    "routes" : (string | number)[][]
                };

                this.state = runStateDiff(this.state, parsedResponse) as typeof this.state;
            }
        } else if (checkKeys(["s_id", "v"], Object.keys(parsedResponse))) {
            const routes_get: Array<Array<string | number>> = stream_mappings[parsedResponse["s_id"]];
            for (const route_get of routes_get) {
                toolchain_state = appendInRoute(toolchain_state, route_get, parsedResponse["v"]);
            }
        } else if (checkKeys(["event_result"], Object.keys(parsedResponse))) {
            final_output = parsedResponse["event_result"];
        }
    }



    // Rest of the class implementation...
}


type Route = Array<string | number>;
// type streamMappingType = {
//     stream_id: string,
//     routes: (string | number)[][]
// }




export function get_value(data: compositionType, 
                          index: number | string): substituteAny {
    if (Array.isArray(data)) {
        return data[index as number];
    } else if (data instanceof Map) {
        if (typeof index !== "string") {
            throw new Error("Index over a map must be a string");
        }
        return data.get(index);
    } else if (typeof data === "object") {
        return data[index as string];
    } else {
        throw new Error("Invalid data type used in get_value");
    }
}


/**
 * Sets the value of an element in the given data structure.
 * 
 * @param data - The data structure to modify.
 * @param index - The index or key of the element to set.
 * @param value - The new value to assign to the element.
 * @returns The modified data structure.
 * @throws {Error} If the data type is invalid or the index is not of the correct type.
 */
export function set_value(
    data: compositionType,
    index: number | string,
    value: substituteAny
): typeof data {
    if (Array.isArray(data)) {
        data[index as number] = value;
    } else if (data instanceof Map) {
        if (typeof index !== "string") {
            throw new Error("Index over a map must be a string");
        }
        data.set(index, value);
    } else if (typeof data === "object") {
        data[index as string] = value;
    } else {
        throw new Error("Invalid data type used in set_value");
    }

    return data;
}


export function delete_value(
    data: compositionType,
    index: number | string
): typeof data {
    if (Array.isArray(data)) {
        data.splice(index as number, 1);
    } else if (data instanceof Map) {
        if (typeof index !== "string") {
            throw new Error("Index over a map must be a string");
        }
        data.delete(index);
    } else if (typeof data === "object") {
        delete data[index as string];
    } else {
        throw new Error("Invalid data type used in delete_value");
    }

    return data;
}


export function appendInRoute(
    objectForStaticRoute: substituteAny,
    route: Route,
    value: substituteAny,
    onlyAdd: boolean = false
): compositionType {
    if (route.length > 0) {

        set_value(objectForStaticRoute as compositionType, route[0], appendInRoute(
            get_value(objectForStaticRoute as compositionType, route[0]) as compositionType,
            route.slice(1),
            value,
            onlyAdd
        ));
    
    } else {
        if (onlyAdd) {
            if (Array.isArray(objectForStaticRoute)) {
                objectForStaticRoute.push(value);
            } else if (typeof objectForStaticRoute === "string") {
                objectForStaticRoute += value as string;
            } else {
                // Throw error
                throw new Error("Invalid data type used in appendInRoute");
            }
        } else if (Array.isArray(objectForStaticRoute)) {
            objectForStaticRoute.push(value);
        } else {

            if (typeof objectForStaticRoute === "string") {
            
                objectForStaticRoute += value;
            } else if (Array.isArray(objectForStaticRoute)) {
                objectForStaticRoute.push(value);
            }
        }
    }

    return objectForStaticRoute as compositionType;
}

export function retrieveValueFromObj(
    input: compositionType,
    directory: string | number | (string | number)[]
): substituteAny {
    try {
        if (typeof directory === "string" || typeof directory === "number") {
            return get_value(input, directory);
        } else {
            let currentDict : compositionType = input;
            for (const entry of directory) {
                currentDict = get_value(currentDict, entry) as compositionType;
            }
            return currentDict;
        }
    } catch (error) {
        throw new Error("Key not found");
    }
}

type deleteStateDictionaryType = string | number | { [key: string]: string | number | deleteStateDictionaryType };

export function runDeleteState(
    stateInput: compositionType,
    deleteStates: deleteStateDictionaryType[] | deleteStateDictionaryType
): typeof stateInput {
    if (Array.isArray(deleteStates)) {
        for (const deleteState of deleteStates) {
            stateInput = runDeleteState(stateInput, deleteState);
        }
        return stateInput;
    } else if (typeof deleteStates === "string" || typeof deleteStates === "number") {
        stateInput = delete_value(stateInput, deleteStates) as typeof stateInput;
    } else {
        stateInput = runDeleteState(stateInput, deleteStates);
    }

    return stateInput;
}



export function updateObjects(
    stateInput: compositionObjectType,
    updateStateInput: compositionObjectType
) : substituteAny {
    if (typeof updateStateInput === "object" && typeof stateInput === "object") {
        stateInput = { ...stateInput, ...updateStateInput };
    } else {
        const updateStateMap = updateStateInput as Map<string, substituteAny>;
        for (const key of updateStateMap.keys()) {
            const updateValue = updateStateMap.get(key) as substituteAny;
            if (typeof updateValue as substituteAny !== "object" && !(updateValue instanceof Map)) {
                stateInput = set_value(
                    stateInput, 
                    key, 
                    updateObjects(
                        get_value(stateInput, key) as compositionObjectType,
                        updateValue as compositionObjectType
                    )
                ) as typeof stateInput;
            }
        }
    }
    return stateInput;
}

export function runStateDiff(
    stateInput: compositionObjectType,
    stateDiffSpecs: {
        appendRoutes?: Route[];
        appendState?: compositionObjectType;
        updateState?: compositionObjectType;
        deleteStates?: deleteStateDictionaryType[];
    }
): typeof stateInput {
    const appendRoutes = stateDiffSpecs.appendRoutes || [];
    const appendState = stateDiffSpecs.appendState || {};
    const updateState = stateDiffSpecs.updateState || {};
    const deleteStates = stateDiffSpecs.deleteStates || [];

    for (const route of appendRoutes) {
        const valGet = retrieveValueFromObj(appendState, route);
        stateInput = appendInRoute(stateInput, route, valGet, true) as typeof stateInput;
    }

    stateInput = updateObjects(stateInput, updateState) as typeof stateInput;

    for (const deleteState of deleteStates) {
        stateInput = runDeleteState(stateInput, deleteState) as typeof stateInput;
    }

    return stateInput;
}

export function checkKeys(keys1: string[], keys2: string[]): boolean {
    return keys1.sort().join() === keys2.sort().join();
}

// export async function wait_for_command_finish(
//     websocket: WebSocket, 
//     toolchain_state: compositionObjectType
// ): Promise<[compositionObjectType, compositionObjectType]> {
    
    

//     while (true) {
//         const response = await websocket.recv();
//         const parsedResponse: compositionObjectType = JSON.parse(response);

//         // console.log(JSON.stringify(parsedResponse, null, 4));
//         if ("ACTION" in parsedResponse && parsedResponse["ACTION"] === "END_WS_CALL") {
//             break;
//         } else {
//             final_output = parsedResponse;
//         }

//         if ("trace" in parsedResponse) {
//             console.log(parsedResponse["trace"]);
//         } else if ("state" in parsedResponse) {
//             toolchain_state = parsedResponse["state"];
//         } else if ("type" in parsedResponse) {
//             if (parsedResponse["type"] === "streaming_output_mapping") {
//                 stream_mappings[parsedResponse["stream_id"]] = parsedResponse["routes"];
//             } else if (parsedResponse["type"] === "state_diff") {
//                 toolchain_state = runStateDiff(_.cloneDeep(toolchain_state), parsedResponse);
//             }
//         } else if (checkKeys(["s_id", "v"], Object.keys(parsedResponse))) {
//             const routes_get: Array<Array<string | number>> = stream_mappings[parsedResponse["s_id"]];
//             for (const route_get of routes_get) {
//                 toolchain_state = appendInRoute(toolchain_state, route_get, parsedResponse["v"]);
//             }
//         } else if (checkKeys(["event_result"], Object.keys(parsedResponse))) {
//             final_output = parsedResponse["event_result"];
//         }
//     }

//     return [final_output, toolchain_state];
// }
