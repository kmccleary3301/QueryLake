import { Dispatch } from "react";
import { 
    compositionObjectGenericType,
    // compositionGenericType,
    compositionObjectType, 
    compositionType,
    substituteAny 
} from "@/typing/toolchains";
import { SERVER_ADDR_WS } from "@/config_server_hostnames";

type stateSet = Dispatch<React.SetStateAction<Map<string, substituteAny>>> | ((new_state : Map<string, substituteAny>) => void)
type titleSet = Dispatch<React.SetStateAction<string>> | ((new_state : string) => void)
// type deleteStateElements = string | number | Array<string | number | compositionObjectGenericType<substituteAny>>;
type deleteStateListType = Array<string | number | compositionObjectGenericType<substituteAny>>;
type deleteStateGenericType = string | number | compositionObjectGenericType<substituteAny>;

export default class ToolchainSession {
    private onStateChange: stateSet;
    private onTitleChange: titleSet;
    private socket: WebSocket; // Add socket as a type
    private state: Map<string, substituteAny>;
    private stream_mappings: Map<string, (string | number)[][]>;
    
    constructor ( onStateChange: stateSet, 
                  onTitleChange: titleSet ) {
        
        this.onStateChange = onStateChange;
        this.onTitleChange = onTitleChange;
        this.socket = new WebSocket(`${SERVER_ADDR_WS}/toolchain`);
        
        this.state = new Map<string, substituteAny>();
        this.stream_mappings = new Map<string, (string | number)[][]>();
        
        

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
        
        if (Object.prototype.hasOwnProperty.call(data, "ACTION") && get_value(data, "ACTION") === "END_WS_CALL") {
            // Rest this.stream_mappings to an empty map
            this.stream_mappings = new Map<string, (string | number)[][]>();
        } else if (Object.prototype.hasOwnProperty.call(data, "trace")) {
            console.log(data);
        } else if ("state" in data) {
            this.state = data["state"] as Map<string, substituteAny>;
        } else if ("type" in data) {

            if (data["type"] === "streaming_output_mapping") {
                const data_typed = data as {"type" : "streaming_output_mapping", "stream_id" : string, "routes" : (string | number)[][]};
                this.stream_mappings.set(data_typed["stream_id"], data_typed["routes"]);
            } else if (data["type"] === "state_diff") {
                const data_typed = data as {
                    type : "state_diff",
                    appendRoutes?: Route[];
                    appendState?: compositionObjectType;
                    updateState?: compositionObjectType;
                    deleteStates?: deleteStateListType;
                };

                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                const { type , ...data_typed_type_removed } = data_typed;

                this.state = runStateDiff(this.state, data_typed_type_removed) as typeof this.state;
                this.onStateChange(this.state);
                this.onTitleChange(get_value(this.state, "title") as string);
            }
        } else if (checkKeys(["s_id", "v"], Object.keys(data))) {
            const data_typed = data as { s_id : string, v : substituteAny };

            // const routes_get: Array<Array<string | number>> = stream_mappings[parsedResponse["s_id"]];
            const routes_get = this.stream_mappings.get(data_typed["s_id"]) as (string | number)[][];
            for (const route_get of routes_get) {
                this.state = appendInRoute(this.state, route_get, data_typed["v"]) as typeof this.state;
            }

            this.onStateChange(this.state);
            this.onTitleChange(get_value(this.state, "title") as string);

        } else if (checkKeys(["event_result"], Object.keys(data))) {
            // TODO: Find a way to return the event result.

            const data_typed = data as { event_result : compositionObjectType };
            // final_output = parsedResponse["event_result"];
            console.log("Event result:", data_typed["event_result"]);
        }
    }

    send_message(message : { [key : string] : substituteAny }) {
        this.socket.send(JSON.stringify(message));
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

export function runDeleteState(
    stateInput: compositionType,
    deleteStates: deleteStateGenericType
): typeof stateInput {
    if (Array.isArray(deleteStates)) {
        for (const deleteState of deleteStates) {
            stateInput = runDeleteState(stateInput, deleteState);
            console.log("State input after array delete with pair", deleteState, ": ", JSON.stringify(stateInput))
        }
    // deleteStates is a map
    // } else if (deleteStates instanceof Map) {
        // for (const key of deleteStates.keys()) {
        //     // stateInput = delete_value(stateInput, key) as typeof stateInput;
        //     stateInput = runDeleteState(stateInput, key) as typeof stateInput;
        // }
    // deleteStates is an object
    } else if (typeof deleteStates === "object") {

        for (const [key, value] of Object.entries(deleteStates)) {
            // stateInput = delete_value(stateInput, key) as typeof stateInput;
            stateInput = set_value(
                stateInput, 
                key, 
                runDeleteState(
                    get_value(stateInput, key) as compositionType, value
                )
            ) as typeof stateInput;
            console.log("State input after object delete with pair", key, value, ": ", JSON.stringify(stateInput))

        }
    // } else if (typeof deleteStates === "string" || typeof deleteStates === "number") {
        
    } else {
        stateInput = delete_value(stateInput, deleteStates) as typeof stateInput;
        console.log("State input after delete of key", deleteStates, ": ", JSON.stringify(stateInput))
    }

    return stateInput;
}




/*
 * This function updates the stateInput with the updateStateInput, same as python dict.update()
 * Needs to account for mixed types of objects and maps.
 */
export function updateObjects(
    stateInput: compositionObjectType,
    updateStateInput: compositionObjectType
) : substituteAny {
    if (typeof updateStateInput === "object" && typeof stateInput === "object") {
        for (const [key, value] of Object.entries(updateStateInput)) {

            if (typeof value === "object" && typeof get_value(stateInput, key) === "object") {
                stateInput = set_value(
                    stateInput,
                    key,
                    updateObjects(
                        get_value(stateInput, key) as compositionObjectType,
                        value as compositionObjectType
                    )
                ) as typeof stateInput;
            } else {
                stateInput = set_value(stateInput, key, value) as typeof stateInput;
            }
        }
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
        deleteStates?: deleteStateListType;
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
    console.log("State input after append:", JSON.stringify(stateInput))

    stateInput = updateObjects(stateInput, updateState) as typeof stateInput;
    console.log("State input after update:", JSON.stringify(stateInput))


    for (const deleteState of deleteStates) {
        stateInput = runDeleteState(stateInput, deleteState) as typeof stateInput;
    }
    console.log("State input after delete:", JSON.stringify(stateInput))

    return stateInput;
}

export function checkKeys(keys1: string[], keys2: string[]): boolean {
    return keys1.sort().join() === keys2.sort().join();
}


export function runUnitTestForDiffFunctions() {
    const dict1 = {'a': 1, 'b': {'x': 'hello!!', 'y': [1, 2, 3]}, 'c': 'world_2', 'e': {'x': 2, 'y': 3}, 'f': {'x': 2}, 'z': 6};
    
    const dict2 = {'b': {'x': 'hello'}, 'c': 'world', 'd': 4, 'f': {'x': 2, 'y': 3}, 'z': 6};

    const dict2Map = new Map(Object.entries(dict2));

    const diff_append_routes = [['b', 'x'], ['c']] ;
    const diff_append = {'b': {'x': '!!'}, 'c': '_2'} ;
    const diff_update = {'a': 1, 'b': {'y': [1, 2, 3]}, 'e': {'x': 2, 'y': 3}} ;
    const diff_delete = ['d', {'f': ['y']}] ;

    const result = runStateDiff(dict2Map, {
        appendRoutes: diff_append_routes, 
        appendState: diff_append, 
        updateState: diff_update, 
        deleteStates: diff_delete
    });

    if (result === dict1) {
        console.log("Test passed");
    } else {
        console.error("Test failed");
        console.error("Expected:", JSON.stringify(dict1));
        console.error("Got:", result);
    }

}