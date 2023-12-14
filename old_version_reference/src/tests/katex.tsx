import React from 'react';
import { View } from 'react-native';
import { bool, func, object, string } from 'prop-types';
import WebView from 'react-native-webview';

function getContent(inlineStyle, expression, options) {
  return `<!DOCTYPE html>
<html>
  <head>
    <style>${inlineStyle}</style>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.10.0-rc.1/dist/katex.min.css" integrity="sha384-D+9gmBxUQogRLqvARvNLmA9hS2x//eK1FhVb9PiU86gmcrBrJAQT8okdJ4LMp2uv" crossorigin="anonymous">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.10.0-rc.1/dist/katex.min.js" integrity="sha384-483A6DwYfKeDa0Q52fJmxFXkcPCFfnXMoXblOkJ4JcA8zATN6Tm78UNL72AKk+0O" crossorigin="anonymous"></script>
  </head>
  <body>
  </body>
  <footer>
    <script>
      window.onerror = e => document.write(e);
      document.addEventListener("DOMContentLoaded", function() {katex.render(${JSON.stringify(expression)}, document.body, ${JSON.stringify(options)});});
    </script>
  </footer>
</html>
`;
}

const defaultStyle = {
  height: 'auto',
  width: 'auto',
  backgroundColor: 'rgba(52, 52, 52, 0)', //transparent background
};

//will center the KaTeX within our webview & view container
const defaultInlineStyle = `
html, body {
  margin: 0;
  padding: 0;
  display:flex;
  justify-content: center;
  align-items: center;
}
`;

class Katex extends React.Component {

  render() {
    const { style, onLoad, onError, inlineStyle, expression, ...options } = this.props;
    const width = expression.length * 8.5 // hacky attempt at dynamic width as flex width wasn't working
    return (
      <View style={{height:40, width:width}}> //approximate line height
        <WebView
          style={style}
          source={{ html: getContent(inlineStyle, expression, options) }}
          onLoad={onLoad}
          onError={onError}
          renderError={onError}
        />
      </View>
    );
  }
}

Katex.propTypes = {
    expression: string.isRequired,
    style: object,
    displayMode: bool,
    throwOnError: bool,
    errorColor: string,
    inlineStyle: string,
    macros: object,
    colorIsTextColor: bool,
    onLoad: func,
    onError: func,
  };

Katex.defaultProps = {
    displayMode: false,
    throwOnError: false,
    errorColor: '#f00',
    inlineStyle: defaultInlineStyle,
    style: defaultStyle,
    macros: {},
    colorIsTextColor: false,
    onLoad: () => {},
    onError: (e) => {console.error(e);},
  };

export default Katex;