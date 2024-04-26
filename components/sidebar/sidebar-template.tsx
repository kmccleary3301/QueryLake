"use client";
import { usePathname } from "next/navigation";
import { useState, useEffect } from 'react';
import { Button } from '@/registry/default/ui/button';
import { useContextAction } from "@/app/context-provider";
import { motion, useAnimation } from "framer-motion";
import * as Icon from 'react-feather';
import { cn } from '@/lib/utils';
import Link from 'next/link';

export default function SidebarTemplate({ 
	children,
	width = "320px",
  className = "",
  buttonsClassName = ""
}:{ 
	children: React.ReactNode,
	width?: string | number,
  className?: string,
  buttonsClassName?: string,
}) {
  const pathname = usePathname();
  const { 
    userData,
  } = useContextAction();


  const width_as_string = (typeof width === 'string') ? `[${width}]` : width.toString();

  const controlsSidebarWidth = useAnimation();
  const [sidebarOpened, setSidebarOpened] = useState<boolean>(false);
  const [sidebarToggleVisible, setSidebarToggleVisible] = useState<boolean>(true);
  
  const controlSidebarButtonOffset = useAnimation();

  useEffect(() => {
		controlsSidebarWidth.start({
			width: 0
		});
	}, [controlsSidebarWidth]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setSidebarToggleVisible(!sidebarOpened);
      controlSidebarButtonOffset.set({ zIndex: sidebarOpened?0:52 });
    }, sidebarOpened?0.4:0);

    controlsSidebarWidth.start({
      width: (sidebarOpened)?width:0,
      transition: { duration: 0.4, ease: "easeInOut", bounce: 0 }
    });

    return () => {
      clearTimeout(timeoutId);
    };
	}, [userData, sidebarOpened, controlsSidebarWidth, controlSidebarButtonOffset]);


  useEffect(() => {
    console.log("TOGGLE VISIBLE:", sidebarToggleVisible)
  }, [sidebarToggleVisible, pathname]);


  useEffect(() => {
    // const sidebar_value = (sidebarIsAvailable && sidebarOpened)?true:false;

    controlSidebarButtonOffset.start({
			translateX: sidebarOpened?0:0,
      opacity: sidebarOpened?0:1,
			transition: { delay: sidebarOpened?0:0.4, duration: sidebarOpened?0:0.6, ease: "easeInOut", bounce: 0 }
		});
  }, [sidebarOpened, controlSidebarButtonOffset, pathname]);


	return (

    <>
      <motion.div 
        id="SIDEBARBUTTON" 
        className={`p-1 pl-2 absolute`}
        initial={{translateX: 0, opacity: 1, zIndex: 52}}
        animate={controlSidebarButtonOffset}>
        {(sidebarToggleVisible) ? (
          <Button variant="ghost" className={`p-2 rounded-md pl-2 pr-2`} onClick={() => {setSidebarOpened(true);}}>
            <Icon.Sidebar id="closed_sidebar_button" size={24}/>
          </Button> 
        ):null}
      </motion.div>
      
      <div className="h-screen">
        <motion.div className="bg-background h-full flex flex-col p-0 z-54" initial={{width: 0}} animate={controlsSidebarWidth} >
          {(userData === undefined) ? (
            null
          ) : (
          <div className='w-full h-full border-r-[1px] border-accent'>
            <div className={cn('max-h-screen h-full flex flex-col', `w-${width_as_string}`, className)}>
              {/* <div className="flex-grow px-0 flex flex-col"> */}
                <div className={cn("flex flex-row pt-1 pb-[7.5px] px-30 items-center w-full justify-between", buttonsClassName)}>
                  <Link href="/home">
                    <Button variant="ghost" className="p-2 rounded-md pl-2 pr-2">
                      <Icon.Home size={24}/>
                    </Button>
                  </Link>
                  <Link href="/settings">
                    <Button variant="ghost" className="p-2 rounded-md pl-2 pr-2">
                      <Icon.Settings size={24}/>
                    </Button>
                  </Link>
                  <Button variant="ghost" className="p-2 rounded-md pl-2 pr-2" onClick={() => {
                    // TODO: Toggle Sidebar
                    setSidebarOpened(false);
                  }}>
                    {/* <Icon.Sidebar size={24} color="#E8E3E3" /> */}
                    <Icon.Sidebar size={24}/>
                  </Button>
                </div>
                <div className='w-full h-[calc(100vh-52px)] flex flex-col'>
                  {children}
                </div>
              {/* </div> */}
            </div>
          </div>
          )}
        </motion.div>
      </div>
    </>
	);
}
