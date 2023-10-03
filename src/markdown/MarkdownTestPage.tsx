import { useState, useRef, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from "expo-font";
import {
  View,
  Text,
  Pressable,
  TextInput,
  StatusBar,
  Modal,
  Button,
  Alert,
  Platform,
  Animated,
  Easing
} from "react-native";
import Clipboard from "@react-native-clipboard/clipboard";
import { Feather } from "@expo/vector-icons";
import { ScrollView, Switch } from "react-native-gesture-handler";
// import Uploady, { useItemProgressListener } from '@rpldy/uploady';
// import UploadButton from "@rpldy/upload-button";
import EventSource from "../react-native-server-sent-events";
import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";
import Icon from "react-native-vector-icons/FontAwesome";
import ChatBarInputWeb from "../components/ChatBarInputWeb";
import ChatBarInputMobile from "../components/ChatBarInputMobile";
import ChatBubble from "../components/ChatBubble";
import { DrawerActions } from "@react-navigation/native";
import MarkdownTestComponent from "../components/MarkdownTestComponent";
import MarkdownRenderer from "./MarkdownRenderer";
// import MarkdownRender from "../components/MarkdownTestComponent";

type CodeSegmentExcerpt = {
  text: string,
  color: string,
};

type CodeSegment = CodeSegmentExcerpt[];

type ChatContentExcerpt = string | CodeSegment;

type ChatContent = ChatContentExcerpt[];

type ChatEntry = {
  origin: ("user" | "server"),
  content: ChatContent,
  content_raw_string: string,
};

type MarkdownTestPageProps = {
  navigation?: any,
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
}


export default function MarkdownTestPage(props : MarkdownTestPageProps) {

  const translateSidebarButton = useRef(new Animated.Value(0)).current;
  const opacitySidebarButton = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(translateSidebarButton, {
      toValue: props.sidebarOpened?-320:0,
      // toValue: opened?Math.min(300,(children.length*50+60)):50,
      duration: 400,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
    setTimeout(() => {
      Animated.timing(opacitySidebarButton, {
        toValue: props.sidebarOpened?0:1,
        // toValue: opened?Math.min(300,(children.length*50+60)):50,
        duration: props.sidebarOpened?50:300,
        easing: Easing.elastic(0),
        useNativeDriver: false,
      }).start();
    }, props.sidebarOpened?0:300);
  }, [props.sidebarOpened]);

  return (
    <View style={{
      flex: 1,
      flexDirection: "row",
      backgroundColor: "#23232D",
      alignItems: "center",
      justifyContent: "center",
      // width: "80vw"
      height: "100vh",
      // width: "100%",
    }}>
      <View style={{flexDirection: 'column', height: '100%', width: '100%', alignItems: 'center'}}>
        <View id="ChatHeader" style={{
          width: "100%",
          height: 40,
          backgroundColor: "#23232D",
          flexDirection: 'row',
          alignItems: 'center'
        }}>
          <Animated.View style={{
            paddingLeft: 10,
            transform: [{ translateX: translateSidebarButton,},],
            elevation: -1,
            zIndex: -1,
            opacity: opacitySidebarButton,
          }}>
            {props.sidebarOpened?(
              <Feather name="sidebar" size={24} color="#E8E3E3" />
            ):(
              <Pressable style={{padding: 0}} onPress={() => {if (props.toggleSideBar) { props.toggleSideBar(); }}}>
                <Feather name="sidebar" size={24} color="#E8E3E3" />
              </Pressable> 
            )}
          </Animated.View>
          {/* Decide what to put here */}
        </View>
        <View style={{
          flexDirection: "column",
          flex: 1,
          // height: "100%",
          width: "88%",
          paddingHorizontal: 0,
          // paddingVertical: 24,
        }}>
          <ScrollView 
            style={{
              flex: 5,
            }}
          >
            <MarkdownRenderer input={MARKDOWN_TEST_2}/>
            
          </ScrollView>

          

        </View>
      </View>
    </View>
  );
}

const MARKDOWN_TEST_MESSAGE = `
# Heading level 1

This is the first paragraph.

This is the second paragraph.

This is the third paragraph.

## Heading level 2

This is an [anchor](https://github.com).

### Heading level 3

This is **bold** and _italics_.

#### Heading level 4

This is \`inline\` code.

This is a code block:

\`\`\`tsx
const Message = () => {
  return <div>hi</div>;
};
\`\`\`

##### Heading level 5

This is an unordered list:

- One
- Two
- Three, and **bold**

This is an ordered list:

1. One
1. Two
1. Three

This is a complex list:

1. **Bold**: One
    - One
    - Two
    - Three
  
2. **Bold**: Three
    - One
    - Two
    - Three
  
3. **Bold**: Four
    - One
    - Two
    - Three

###### Heading level 6

> This is a blockquote.

This is a table:

| Vegetable | Description |
|-----------|-------------|
| Carrot    | A crunchy, orange root vegetable that is rich in vitamins and minerals. It is commonly used in soups, salads, and as a snack. |
| Broccoli  | A green vegetable with tightly packed florets that is high in fiber, vitamins, and antioxidants. It can be steamed, boiled, stir-fried, or roasted. |
| Spinach   | A leafy green vegetable that is dense in nutrients like iron, calcium, and vitamins. It can be eaten raw in salads or cooked in various dishes. |
| Bell Pepper | A colorful, sweet vegetable available in different colors such as red, yellow, and green. It is often used in stir-fries, salads, or stuffed recipes. |
| Tomato    | A juicy fruit often used as a vegetable in culinary preparations. It comes in various shapes, sizes, and colors and is used in salads, sauces, and sandwiches. |
| Cucumber   | A cool and refreshing vegetable with a high water content. It is commonly used in salads, sandwiches, or as a crunchy snack. |
| Zucchini | A summer squash with a mild flavor and tender texture. It can be sautéed, grilled, roasted, or used in baking recipes. |
| Cauliflower | A versatile vegetable that can be roasted, steamed, mashed, or used to make gluten-free alternatives like cauliflower rice or pizza crust. |
| Green Beans | Long, slender pods that are low in calories and rich in vitamins. They can be steamed, stir-fried, or used in casseroles and salads. |
| Potato | A starchy vegetable available in various varieties. It can be boiled, baked, mashed, or used in soups, fries, and many other dishes. |

This is a mermaid diagram:

\`\`\`mermaid
gitGraph
    commit
    commit
    branch develop
    checkout develop
    commit
    commit
    checkout main
    merge develop
    commit
    commit
\`\`\`

\`\`\`latex
\\[F(x) = \\int_{a}^{b} f(x) \\, dx\\]
\`\`\`
`;

const MARKDOWN_TEST_2 = `
# Introduction to Naive Bayes Classifier 
The Naive Bayes classifier is a simple probabilistic classifier that is based on Bayes' theorem. It is called "naive" because it assumes that the features are independent of each other, which is often not true in real-world datasets. Despite its simplicity, the Naive Bayes classifier has been shown to perform well in many applications, including text classification, image classification, and bioinformatics. In this set of notes, we will cover the basics of the Naive Bayes classifier, including how it works, how to train it, and how to use it for classification. 
## How does Naive Bayes work? 
The Naive Bayes classifier works by estimating the probability of an instance belonging to each class given the feature values. The probability is calculated using Bayes' theorem, which states that the probability of a hypothesis (H) given some evidence (E) is equal to the probability of the evidence given the hypothesis multiplied by the prior probability of the hypothesis divided by the normalizing constant. In the case of the Naive Bayes classifier, the hypothesis is the class label, and the evidence is the vector of feature values. 
$$P(y|x) = \\frac{P(x|y) \\cdot P(y)}{P(x)}$$
Where $y$ is the class label, $x$ is the input feature vector, $P(y|x)$ is the posterior probability of the class label given the input feature vector, $P(x|y)$ is the likelihood of the input feature vector given the class label, and $P(y)$ is the prior probability of the class label. To calculate the posterior probability, we need to compute the likelihood of the input feature vector given the class label first. This can be done using the following formula: $$P(x|y) = \\prod_{i=1}^n \\frac{f_i(x_i | y)}{f_i(x_i)}$$ Where $f_i(x_i | y)$ is the probability of the $i^{th}$ feature value given the class label, and $f_i(x_i)$ is the prior probability of the $i^{th}$ feature value. Once we have the posterior probability, we can use it to make predictions on new instances. We do this by calculating the probability of each class given the input feature vector and selecting the class with the highest probability as the predicted label.
## How to train a Naive Bayes Classifier
Training a Naive Bayes classifier involves estimating the parameters of the model using the training data. The parameters are the prior probabilities of each class and the conditional probabilities of each feature given the class label. These parameters are used to compute the posterior probability of the class label given the input feature vector. There are several ways to estimate the parameters of a Naive Bayes classifier, including: 
* Using the maximum entropy method, which maximizes the entropy of the posterior distribution over the classes given the input features. * Using the Expectation-Maximization (EM) algorithm, which alternates between computing the expected values of the parameters given the training data and updating the parameters based on these expectations. 
* Using the Variational Bayes (VB) algorithm, which approximates the posterior distribution over the parameters using a variational distribution and updates the parameters based on the evidence. Once the parameters are estimated, they can be used to make predictions on new instances. 
## Advantages and Disadvantages of Naive Bayes Advantages: 
* Simple to implement and interpret
* Can handle missing values 
* Robust to outliers and noisy data 
* Fast computation time Disadvantages: 
* Assumes independence of features, which is often not true in real-world datasets 
* Can be sensitive to irrelevant features 
* Not suitable for high-dimensional data 
* May not perform well when the number of classes is large 
In conclusion, the Naive Bayes classifier is a simple probabilistic classifier that has been widely used in many applications. It assumes that the features are independent of each other, which may not always be true in real-world datasets. However, it has several advantages, such as being easy to implement and interpret, handling missing values, and being robust to outliers and noisy data. Despite its limitations, the Naive Bayes classifier remains a popular choice for classification tasks due to its simplicity and effectiveness.


Lecture Notes: Naive Bayes Classifier Introduction: The Naive Bayes classifier is a simple probabilistic classifier that is based on Bayes’ theorem. It is called “naive” because it assumes that the features are independent of each other, which is often not true in real-world datasets. Despite its simplicity, the Naive Bayes classifier has been shown to perform well in many applications, including text classification, image classification, and bioinformatics. Math Expressions: To understand how the Naive Bayes classifier works, let’s start by defining some mathematical notation. Let $X$ be the feature matrix, where each row represents a sample and each column represents a feature. Let $Y$ be the label vector, where each element $y_i$ represents the class of the $i^{th}$ sample. Let $p(x)$ be the prior probability distribution over the features, and let $p(y|x)$ be the conditional probability distribution over the
`;
