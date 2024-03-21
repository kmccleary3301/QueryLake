"use client";
import { useContextAction } from "@/app/context-provider";


export const ContextTestDisplay = ({
  className,
}: {
  className?: string
}) => {
  const { userData } = useContextAction();

  return (
    <div className={className}>
      Current context is
      <p className="text-sm font-thin">{JSON.stringify(userData)}</p>
    </div>
  );
};
