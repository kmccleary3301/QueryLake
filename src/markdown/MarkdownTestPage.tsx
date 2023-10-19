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
import AnimatedPressable from "../components/AnimatedPressable";

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

  const test_auth_login = () => {
    const url = new URL("http://localhost:5000/api/login");
    url.searchParams.append("name", "John_5817263");
    url.searchParams.append("password", "John_5817263");
    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
          console.log(data);
      });
    });
  };

  const test_auth_add_account = () => {
    const url = new URL("http://localhost:5000/api/create_account");
    url.searchParams.append("name", "John_5817263");
    url.searchParams.append("password", "John_5817263");
    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
          console.log(data);
      });
    });
  };

  const test_auth_hash = () => {
    const url = new URL("http://localhost:5000/api/auth");
    url.searchParams.append("input", "John_5817263");
    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
          console.log(data);
      });
  });
  };

  return (
    <View style={{
      flex: 1,
      flexDirection: "row",
      backgroundColor: "#23232D",
      alignItems: "center",
      justifyContent: "center",
      // width: "80vw"
      height: "100vh",
      paddingRight: 10, 
      width: "100%",
      // backgroundColor: "#3939FF",
      // borderRadius: 10,
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
              <AnimatedPressable style={{padding: 0}} onPress={() => {if (props.toggleSideBar) { props.toggleSideBar(); }}}>
                <Feather name="sidebar" size={24} color="#E8E3E3" />
              </AnimatedPressable> 
            )}
          </Animated.View>
          <AnimatedPressable style={{padding: 0}} onPress={test_auth_hash}>
            <Feather name="key" size={24} color="#E8E3E3" />
          </AnimatedPressable> 
          <AnimatedPressable style={{padding: 0}} onPress={test_auth_add_account}>
            <Feather name="plus" size={24} color="#E8E3E3" />
          </AnimatedPressable>
          <AnimatedPressable style={{padding: 0}} onPress={test_auth_login}>
            <Feather name="log-in" size={24} color="#E8E3E3" />
          </AnimatedPressable> 
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
            <MarkdownRenderer input={MARKDOWN_TEST_MESSAGE}/>
            
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

This is **bold** and *italics*.

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

### Jacobian $f: \\mathbb{R}^n \\to \\mathbb{R}^m$

The Jacobian of a function is a matrix that represents the partial derivatives of the function's output variables with respect to its input variables. It is a powerful tool in multivariate calculus and is used in many areas of mathematics, science, and engineering. In mathematical notation, the Jacobian of a function $f: \\mathbb{R}^n \\to \\mathbb{R}^m$ at a point $\\mathbf{x} = (x_1, \\ldots, x_n)$ is denoted by $\\mathbf{J}_f(\\mathbf{x})$ and has dimensions $m \\times n$. Its entries are given by: $$\\mathbf{J}_f(\\mathbf{x}) = \\begin{bmatrix} \\frac{\\partial f_1}{\\partial x_1} & \\frac{\\partial f_1}{\\partial x_2} & \\cdots & \\frac{\\partial f_1}{\\partial x_n} \\\\ \\vdots & \\vdots & \\ddots & \\vdots \\\\ \\frac{\\partial f_m}{\\partial x_1} & \\frac{\\partial f_m}{\\partial x_2} & \\cdots & \\frac{\\partial f_m}{\\partial x_n} \\end{bmatrix}$$ where $f_i$ is the $i$th component of the vector-valued function $f$. The Jacobian can be used to linearize the behavior of a function near a point, which can be useful for optimization problems or other applications where you want to approximate the behavior of a function locally. It can also be used to compute the differential of a function, which is important in many areas of mathematics and physics.

Magma (in group theory)
=====================

A magma in group theory is an algebraic structure consisting of a set of elements together with two binary operations (usually called multiplication and addition) that satisfy certain axioms. The term "magma" was introduced by John H. Conway as a more generalization of the concept of a group, which he defined as a special kind of magma with additional properties.
Definition of a magma
-------------------------

Formally, a magma M consists of a set X together with two binary operations + and ·, such that the following axioms are satisfied:
1. Closure under +: For all a, b in X, a + b is also in X.
2. Associativity: For all a, b, c in X, (a + b) + c = a + (b + c).
3. Identity: There exists an element 0 in X, such that for any a in X, a + 0 = a.
4. Inverse: For each element a in X, there exists an element -a in X, such that a + (-a) = 0.
Note that these axioms are similar to those defining a group, but they do not include the requirement that the operation must be commutative or have an identity element.
Examples of magmas
--------------

Many examples of magmas can be found in mathematics, particularly in abstract algebra and combinatorics. Here are some common ones:
1. Vector spaces: A vector space over a field F forms a magma under vector addition and scalar multiplication.
2. Groups: As mentioned earlier, a group is a special type of magma where the operation is commutative and has an identity element.
3. Rings: A ring is a mathematical structure consisting of a set of elements together with two binary operations (usually called addition and multiplication) that satisfy certain axioms. Rings form a magma under ring addition and multiplication.
4. Algebras: An algebra is a mathematical structure consisting of a set of elements together with two binary operations (usually called multiplication and addition) that satisfy certain axioms. Algebras form a magma under algebra multiplication and addition.
5. Quotient magmas: Given a magma M, we can define a new magma Q by identifying certain elements of M as "equivalent" and forming a quotient set. This construction can be used to study various algebraic structures, including groups, rings, and algebras.
Properties of magmas
-------------------------

Magmas share many properties with groups, but there are also some important differences. Some key properties of magmas include:
1. Non-associativity: Unlike groups, which are associative under their operation, magmas do not necessarily have this property.
2. Lack of closure under multiplication: Magmas do not have closure under multiplication, meaning that the product of two elements need not always exist in the magma.
3. No identity element for multiplication: While magmas have an identity element for addition, they do not necessarily have one for multiplication.
4. No inverse for each element: In contrast to groups, where every element has an inverse, magmas may or may not have an inverse for each element.
Applications of magmas
--------------

Magmas have found applications in various areas of mathematics and computer science, including:

1. Combinatorics: Magmas are used to study combinatorial objects such as graphs, posets, and designs.
2. Computer science: Magmas are used in programming languages, compilers, and other computational systems.
3. Cryptography: Magmas are used in cryptographic protocols, such as public-key encryption and digital signatures.
4. Algebraic geometry: Magmas are used to study geometric objects defined by polynomial equations.
Conclusion
----------

In conclusion, magmas are algebraic structures that generalize groups and provide a framework for studying various mathematical concepts. They offer a powerful tool for solving problems in algebra, combinatorics, and computer science, among other fields. By understanding magmas, we can gain insights into the structure and behavior of these mathematical objects and develop new techniques for working with them.

# Naive Bayes Classifier

The Naive Bayes classifier is a simple probabilistic classifier that is based on Bayes' theorem. It is called "naive" because it assumes that the features are independent of each other, which is often not true in real-world datasets. Despite its simplicity, the Naive Bayes classifier has been shown to perform well in many applications, including text classification, image classification, and bioinformatics. In this set of notes, we will provide an overview of the Naive Bayes classifier, its strengths and weaknesses, and how it can be used in practice.
## How does the Naive Bayes classifier work?

The Naive Bayes classifier works by estimating the probability of an instance belonging to each class given the feature values. The probability is calculated using Bayes' theorem, which states that the probability of a hypothesis (H) given some evidence (E) is equal to the probability of the evidence given the hypothesis multiplied by the prior probability of the hypothesis divided by the probability of all hypotheses:
$$P(H|E) = \\frac{P(E|H) \\times P(H)}{P(E)}$$
In the case of the Naive Bayes classifier, the hypothesis is represented by a vector of probabilities for each class, and the evidence is represented by a vector of feature values. The Naive Bayes classifier uses a simple trick to simplify the calculation of the posterior probability of the classes given the features: it sets one of the probabilities to 1, effectively eliminating that class from consideration. This allows the classifier to focus on the remaining classes and calculate their probabilities more accurately.
## Strengths of the Naive Bayes classifier


1. **Handling missing values**: The Naive Bayes classifier can handle missing values in the data, which is a common problem in many machine learning tasks. It simply ignores the missing values when calculating the probabilities.
2. **Scalability**: The Naive Bayes classifier is very scalable, as it only requires computing the probabilities of each class given the features for each instance. This makes it well-suited for large datasets where computational resources are limited.
3. **Interpretability**: The Naive Bayes classifier provides interpretable results, as the probabilities of each class given the features provide insight into how the classifier has made its prediction.
4. **Robustness**: The Naive Bayes classifier is robust to outliers and noisy data, as it calculates the probabilities based on the entire dataset rather than just the instances with the most extreme features.
5. **Flexibility**: The Naive Bayes classifier can be used for both binary and multiclass classification problems, and it can handle categorical variables directly without requiring any additional preprocessing steps.

## Weaknesses of the Naive Bayes classifier


1. **Assumes independence**: The Naive Bayes classifier assumes that the features are independent of each other, which is often not true in real-world datasets. In fact, many datasets exhibit complex relationships between the features, which can lead to poor performance if these relationships are not captured.
2. **Sensitivity to prior probabilities**: The Naive Bayes classifier relies heavily on the prior probabilities of the classes, which can have a significant impact on its performance. If the prior probabilities are not accurate or fair, the classifier may make suboptimal predictions.
3. **Lack of handling non-linear relationships**: The Naive Bayes classifier assumes linear relationships between the features and the classes, which can lead to poor performance when dealing with non-linear relationships.
4. **Inability to handle high-dimensional data**: As the number of features increases, the computational complexity of the Naive Bayes classifier grows exponentially, making it difficult to apply to high-dimensional data.
5. **Limited adaptability**: Once trained, the Naive Bayes classifier cannot adapt to new data, as it does not learn from the examples it sees. This means that the classifier will perform poorly on unseen data, especially in cases where the distribution of the data changes over time.

## How to use the Naive Bayes classifier in practice


To use the Naive Bayes classifier in practice, follow these steps:

1. **Prepare the data**: Prepare your dataset by splitting it into training and testing sets, and encoding categorical variables if necessary.
2. **Calculate the priors**: Calculate the prior probabilities of each class using the class distribution of the training set. You can use the class labels directly or estimate them using techniques such as k-means clustering.
3. **Train the classifier**: Train the Naive Bayes classifier using the training set, setting one of the probabilities to 1 (usually the class with the highest probability).
4. **Predict on the test set**: Use the trained classifier to predict the classes of the test set.
5. **Evaluate the performance**: Evaluate the performance of the classifier using metrics such as accuracy, precision, recall, F1 score, etc. Compare the results to those obtained using other classification algorithms to determine which one performs better.
6. **Tune the hyperparameters**: Tune the hyperparameters of the classifier, such as the prior probabilities, to improve its performance. This may involve iteratively retraining the classifier with different values for the hyperparameters until you find the best combination.
7. **Deploy the classifier**: Once you are satisfied with the performance of the classifier, deploy it in your application, using it to make predictions on new data based on the features available.

\`\`\`python
from .langchain_sse import CustomStreamHandler, ThreadedGenerator
# from . import Exllama

from langchain.callbacks.manager import CallbackManager
from langchain import PromptTemplate, LLMChain

import threading
import copy

print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

class LLMEnsemble:
    def __init__(self, default_config, model_class) -> None:
        self.max_instances = 1
        self.llm_instances = []
        self.default_config = default_config
        self.model_class = model_class
        self.make_new_instance(self.default_config)
\`\`\`

\`\`\`
// Simple C program to display "Hello World”
// Header file for input output functions
#include <stdio.h>

/*
main function -
where the execution of program begins
*/
int main()
{
  //prints hello world
  printf("Hello World”);
  return 0;
}
\`\`\`

`;
