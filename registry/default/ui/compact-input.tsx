import { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Button } from '@/registry/default/ui/button';
import * as Icon from 'react-feather';

export default function CompactInput({
  className,
  type,
  placeholder,
  ...props
}: {
  className?: string;
  type?: string;
  placeholder?: string;
  [key: string]: any;
}) {
  const [isFocused, setIsFocused] = useState(false);
	const [placeHolderMoved, setPlaceHolderMoved] = useState(false);
	const [hidden, setHidden] = useState((type === "password") ? true : false);

	const height = className ? className.match(/h-(^[\s]+)/)?.[1] : "h-10";

  return (
    <div 
			className={cn(
				"bg-background flex h-10 w-full rounded-md border border-input ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50",
				className, 
				"flex flex-col-reverse mx-0 px-0",
				isFocused ? "border-primary" : "",
			)}
			onFocus={() => {console.log("Focus Called!")}}
		>
			<div className='flex flex-row py-0 px-0 mr-0 h-full rounded-md'>
				<input
					className={
						"border-none p-0 px-3 bg-transparent rounded-md ring-transparent focus-visible:ring-transparent focus-visible:border-none focus:outline-none h-full"
					}
					// type={type}
					type={hidden ? "password" : "text"}
					{...props}
					onFocus={(e) => {
						setIsFocused(true);
						setPlaceHolderMoved(true);
						const currentText = e.target.value;
						console.log("FOCUS:", e, e.target.value);
						if (props && props.onFocus) props.onFocus(e);
					}}
					onBlur={(e) => {
						setIsFocused(false);
						const currentText = e.target.value;
						if (currentText === "") setPlaceHolderMoved(false);
						console.log("BLUR:", e);
						if (props && props.onBlur) props.onBlur(e);
					}}
					spellCheck={false}
					// hidden={true}
				/>
				{(type === "password") && (
					<Button variant={"ghost"} type="button" className={cn(
						"flex-1 border-[3.5px] border-transparent h-auto",
						(isFocused ? "rounded-md" : "rounded-sm"),
						"rounded-l-none px-0"
					)} onClick={() => {
						setHidden(!hidden);
					}}>
						{(hidden) ? <Icon.EyeOff className='w-4 h-4 text-muted-foreground' /> : <Icon.Eye className='w-4 h-4 text-muted-foreground' />}
					</Button>
				)}
			</div>
			<div className="h-0 pointer-events-none placeholder-inherit">
				<div className={cn(
					"h-10 px-3 py-0",
					className,
					"bg-transparent pl-0 text-inherit placeholde-inherit w-auto"
				)} onFocus={()=>{console.log("Focus Called!")}}>
					<motion.div
						className='h-full'
						animate={ (placeHolderMoved) ? 
							{ y: 'calc(0% - 0.75em - 0px)', fontSize: '0.75em', paddingLeft: '0.2rem' } : 
							{ y: 'calc(50% - 1em + 2px)', fontSize: '1em', paddingLeft: '0.5rem'}
						}
						transition={{ duration: 0.2 }}
					>
						<span className={cn("placeholder bg-background px-1 rounded-sm", isFocused?"text-primary":"text-muted-foreground")}>{placeholder}</span>
					</motion.div>
				</div>
			</div>
		</div>
  );
}