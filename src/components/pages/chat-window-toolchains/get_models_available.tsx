import { Dispatch, SetStateAction } from "react";
import { substituteAny } from "@/typing/toolchains";
import { userDataType } from "@/typing/globalTypes";
import craftUrl from "@/hooks/craftUrl";

type modelsAvailableType = {
    label : string, 
    value : string | string[]
}[];

interface getModelsAvailableArgs {
    auth: userDataType,
    setState : (React.Dispatch<React.SetStateAction<Map<string, modelsAvailableType>>>) | ((new_state : Map<string, modelsAvailableType>) => void)
}

export default function getModelsAvailable(args : getModelsAvailableArgs) {
    const url = craftUrl({url: "/get_models_available", auth: args.auth});
    fetch(url)
    .then(response => response.json())
    .then(data => {
        console.log("Data: ", data);
        args.setState(new Map(Object.entries(data)));
    });
}

