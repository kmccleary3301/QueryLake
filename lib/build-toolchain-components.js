const fs = require("fs");
const path = require("path");

const toVariableName = (str) => {
  // Remove non-alphanumeric characters and convert to lower case
  str = str.replace(/\.md$/, "")
  str = str.replaceAll(" ", "_")
  str = str.replaceAll(/[^a-zA-Z0-9_]/g, '').toLowerCase();

  // Split by spaces
  let words = str.split(' ');

  // // Remove any word that starts with a number
  // words = words.filter(word => isNaN(word[0]));

  // Convert to camelCase
  for (let i = 1; i < words.length; i++) {
    words[i] = words[i].charAt(0).toUpperCase() + words[i].slice(1);
  }

  return words.join('').replace(/[\_]+$/, '').replace(/^[\_]+/, '').replaceAll(/[\_]+/g, '_');
}


function generate_component_exports(directory) {
  const files = fs.readdirSync(directory);

  files.forEach(file => {
    const filePath = path.join(directory, file);
    const stats = fs.statSync(filePath);

    if (stats.isDirectory()) {
      readTsxFiles(filePath); // Recurse if directory
    } else if (path.extname(file) === '.tsx') {
      const fileContent = fs.readFileSync(filePath, 'utf-8');
      console.log(fileContent);
    }
  });
}


const COMPONENTS_DIRECTORY = 'app/components/toolchain';

generate_component_exports(COMPONENTS_DIRECTORY);