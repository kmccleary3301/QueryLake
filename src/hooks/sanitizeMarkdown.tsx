

export default function sanitizeMarkdown(input_string : string) {
  
  let ret = input_string;
  let input_split = input_string.split("\n");
  let line_is_table_row = Array(input_split.length).fill(false);
  let line_is_whitespace = Array(input_split.length).fill(false);

  let line_action = Array(input_split.length).fill(0); //0 for nothing, 1 for newline, 2 for deletion

  for (let i = 0; i < input_split.length; i++) {
    let table_match = input_split[i].match(/^([\s]*\|([^\n])+\|[\s]*)$/);
    let whitespace_match = input_split[i].match(/^([\s]*)$/);
    if (whitespace_match !== null) { line_is_whitespace[i] = true; }
    if (table_match !== null) {
      if (i > 0 && !line_is_table_row[i-1]) {
        if (!line_is_whitespace[i-1]) {
          line_action[i] = 1; //Insert empty line before start of table.
        }
        
      } else { 
        if (i > 1 && line_is_whitespace[i-1] && line_is_table_row[i-2]) {
          line_action[i-1] = 2; //Delete empty line between table rows.
        }
      }

      line_is_table_row[i] = true;
    } else {
      if (i > 0 && line_is_table_row[i-1] && !line_is_whitespace[i]) {
        line_action[i] = 1; //Insert empty line after end of table.
      }
    }
  }
  // console.log("Input Split");
  // console.log(input_split);
  // console.log("Line Actions");
  // console.log(line_action);
  // console.log("Line Is Whitespace");
  // console.log(line_is_whitespace);

  for (let i = line_action.length-1; i >= 0; i--) {
    if (line_action[i] === 2) {
      input_split.splice(i, 1);
    } else if (line_action[i] === 1) {
      input_split = [...input_split.slice(0, i), "", ...input_split.slice(i)]; 
    }
  }
  ret = input_split.join("\n");


  // console.log("Rows identified");
  // console.log(line_is_table_row);


  // let ret = input_string
  // .replace(/<\|[a-z]*$/, "")
  // .replace(/<\|[a-z]+\|$/, "")
  // .replace(/<$/, "")
  // // .replaceAll(PUBLIC_SEP_TOKEN, " ")
  // .replaceAll(/<\|[a-z]+\|>/g, " ")
  // .replaceAll(/<br\s?\/?>/gi, "\n")
  // // .replaceAll("<", "&lt;")
  // .trim();

  // for (const stop of [...(model.parameters?.stop ?? []), "<|endoftext|>"]) {
  //   if (ret.endsWith(stop)) {
  //     ret = ret.slice(0, -stop.length).trim();
  //   }
  // }

  return ret;
}