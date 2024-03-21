import { useState, useEffect } from "react";
import { motion } from "framer-motion";
// import openDocumentSecure from "../hooks/openDocumentSecure";
import { openDocumentSecure } from "@/hooks/querylakeAPI";
import { userDataType, metadataDocumentRaw } from "@/typing/globalTypes";

type ChatBubbleSourceProps = {
  icon?: string | ArrayBuffer | Blob,
  userData: userDataType,
  document : string,
  metadata: metadataDocumentRaw & {rerank_score?: number},
};


export default function ChatBubbleSource(props : ChatBubbleSourceProps) {
  const [expanded, setExpanded] = useState(false);
  const [delayedExpanded, setDelayedExpanded] = useState(false);
  // const [trueContentWidth, setTrueContentWidth] = useState(140);
  // const [trueContentHeight, setTrueContentHeight] = useState(60);

  const content_reformat = props.document.replaceAll(/(-[\s]*\n)/g, "").replaceAll(/([\s]*\n)/g, " ");
  const opacity = (props.metadata.rerank_score)?(Math.min(255, Math.floor(255*(Math.sqrt(props.metadata.rerank_score)*0.8 + 0.2))).toString(16).toUpperCase()):"FF";

  useEffect(() => {
    setTimeout(() => {
      setDelayedExpanded(expanded);
    }, expanded?0:250);
  }, [expanded]);

  return (
    <div style={{
      padding: 5
    }}>
      <div onClick={() => {setExpanded(!expanded)}}>
        <motion.div 
          style={{
            borderRadius: 10,
            borderWidth: 2,
            borderColor: (props.metadata.document_name)?"#E50914"+opacity:"#88C285"+opacity,
            backgroundColor: "#17181D",
            padding: 0,
            paddingRight: 4,
            flexDirection: 'column',
          }} 
          animate={{
            width: 6+((expanded)?Math.min(400, 400):140),
            height: 10+((expanded)?200:19),
          }}
          transition={{ duration: 0.25, type: "spring", damping: 20, stiffness: 300 }}
        >
          <div style={{padding: 3}}>
            <div>
              <p 
                style={{
                  // fontFamily: "Inter-Regular",
                  fontSize: 12,
                  color: "#E8E3E3",
                  paddingLeft: 6,
									paddingRight: 6,
									paddingTop: 2,
									paddingBottom: 2,
                  maxWidth: 400
                }}
              >
                {props.metadata.document_name}
              </p>
            </div>
            {(delayedExpanded) && (
              <div>
                <p 
                  style={{
                    fontFamily: "Inter-Regular",
                    fontSize: 12,
                    color: "#E8E3E3",
                    paddingLeft: 6,
										paddingRight: 6,
										paddingTop: 2,
										paddingBottom: 2,
                    maxWidth: 400
                  }}
                >
                  {"Relevance Score: "+((props.metadata.rerank_score !== undefined)?(props.metadata.rerank_score.toString().slice(0, 5)):"N/A")}
                </p>
                <p 
                  style={{
                    fontFamily: "Inter-Regular",
                    fontSize: 12,
                    color: "#E8E3E3",
                    paddingLeft: 6,
										paddingRight: 6,
										paddingTop: 2,
										paddingBottom: 2,
                    maxWidth: 400
                  }}
                >
                  {"Content"}
                </p>
                <motion.div onClick={() => {openDocumentSecure({
									userData: props.userData, 
									metadata: props.metadata
								})}}>
                  <motion.p 
                    style={{
                      fontFamily: "Inter-Thin",
                      fontStyle: 'italic',
                      fontSize: 12,
                      color: "#E8E3E3",
                      paddingLeft: 6,
											paddingRight: 6,
                      paddingTop: 2,
											paddingBottom: 2,
                      maxWidth: 400,
                      textAlign: 'center'
                    }}
                  >
                    {content_reformat}
                  </motion.p>
                </motion.div>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}