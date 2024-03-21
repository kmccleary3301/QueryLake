import MarkdownRenderer from "@/components/markdown/markdown-renderer";
import allDocs from "@/public/cache/documentation/__all-documents__";
import { getValueFromPath } from "./hooks";
import React from "react";

interface DocPageProps {
  params: {
    slug: string[],
  },
  searchParams: object
}

export default function DocPage({ params, searchParams }: DocPageProps) {
  const { slug } = params;
  const doc : { slug : string, content : string } = getValueFromPath(allDocs, slug);

  if (doc === undefined) {
    return (
      <>
        <div className='w-full h-[calc(100vh-60px)] flex flex-col justify-center'>
          <h1>Doc Not Found</h1>
          <p className='w-full text-base text-primary/80 break-words text-left'>
            The doc you are looking for does not exist.  
          </p>
        </div>
      </>
    );
  }

  return (
    <div>
      <p className="text-5xl text-primary/80 text-bold pt-5 pb-10"><strong>{doc.slug}</strong></p>
      {/* <p className="text-lg text-primary text-bold pb-10 pt-5">
        <em>By Kyle McCleary</em>
      </p> */}
      <MarkdownRenderer input={doc.content} finished={true}/>
    </div>
  );
}