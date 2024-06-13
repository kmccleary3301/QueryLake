"use client";
import { cn } from "@/lib/utils";
import React, { useEffect, useRef, useState } from "react";
import { createNoise3D } from "simplex-noise";

const get_point = (magnitude : number, theta : number) => {
  return {
    x: magnitude * Math.cos(theta),
    y: magnitude * Math.sin(theta),
  };
}


export const QueryLakeLogo = ({
  children,
  className,
  containerClassName,
  canvasClassName,
  colors,
  waveWidth,
  backgroundFill,
  blur = 10,
  speed = 5,
  waveOpacity = 0.5,
  waveCount = 5,
  waveAmplitude = 100,
  wavePinchMiddle = 0,
  wavePinchEnd = 0,
  ...props
}: {
  children?: any;
  className?: string;
  containerClassName?: string;
  canvasClassName?: string;
  colors?: string[];
  waveWidth?: number;
  backgroundFill?: string;
  blur?: number;
  speed?: number;
  waveOpacity?: number;
  waveCount?: number;
  waveAmplitude?: number;
  wavePinchMiddle?: number;
  wavePinchEnd?: number;
  [key: string]: any;
}) => {
  const noise = createNoise3D();
  const start_time = Date.now();
  let w: number,
      h: number,
      nt: number,
      i: number,
      x: number,
      ctx: any,
      canvas: any,
      animation_points: number = 40,
      time_passed: number = 0,
      interval : number = 0;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const speedSet = Array.from({length: waveCount}, () => speed * (Math.random() * 0.9 + 0.1));

  const init = () => {
    canvas = canvasRef.current;
    ctx = canvas.getContext("2d");

    let parent = canvas.parentElement;

    // Set the canvas dimensions to match the parent's dimensions
    if (parent) {
      canvas.width = parent.offsetWidth;
      canvas.height = parent.offsetHeight;
      w = ctx.canvas.width = canvas.width;
      h = ctx.canvas.height = canvas.height;
      interval = w / animation_points;
    }

    // ctx.filter = `blur(${blur}px)`;
    nt = 0;
    window.onresize = function () {
      canvas.width = parent.offsetWidth;
      canvas.height = parent.offsetHeight;
      w = ctx.canvas.width = canvas.width;
      h = ctx.canvas.height = canvas.height;
      // w = ctx.canvas.width = window.innerWidth;
      // h = ctx.canvas.height = window.innerHeight;
      interval = w / animation_points;
      // ctx.filter = `blur(${blur}px)`;
    };
    render();
  };

  const waveColors = colors ?? [
    "#38bdf8",
    "#818cf8",
    "#c084fc",
    "#e879f9",
    "#22d3ee",
  ];
  
  // const drawWave = (n: number) => {
  //   time_passed = Date.now() - start_time;
  //   for (i = 0; i < n; i++) {
  //     const lt = speedSet[i] * 0.001 * time_passed * 0.05;
  //     ctx.beginPath();
  //     ctx.lineWidth = waveWidth || 50;
  //     ctx.strokeStyle = waveColors[i % waveColors.length];
  //     for (x = 0; x < w; x += interval) {
  //       const xNormalized = ( x ) / ( w );
  //       const pinchedAmplitude = waveAmplitude * ( (1 - wavePinch) * Math.sin( Math.PI * xNormalized) + wavePinch );

  //       var y = noise(x / 800, 2 * i, lt) * pinchedAmplitude;
  //       ctx.lineTo(x, y + h * 0.5); // adjust for height, currently at 50% of the container
  //     }
  //     ctx.stroke();
  //     ctx.closePath();
  //   }
  // };

  const drawWave = (n: number) => {
    time_passed = Date.now() - start_time;
    let points : number[][][] = [];
    const calc_callbacks = [(n_2 : number) => get_point(waveAmplitude, Math.PI*(2*n_2/n + 1/n))]
    const lt = 0.001 * time_passed * 0.05;
    const R_COUNT = 5

    for (let r = 0; r < R_COUNT; r++){
      ctx.lineWidth = 10;
      ctx.strokeStyle = waveColors[r % waveColors.length];
      if (r === 1) {
        calc_callbacks.push((n_2 : number) => {
          return get_point(waveAmplitude*Math.cos(Math.PI/n), Math.PI*(2*n_2/n));
        })
      } else if (r > 1) {
        calc_callbacks.push((n_2 : number) => {
          const p_1 = calc_callbacks[r-1](n_2),
                p_2 = calc_callbacks[r-1](n_2 + 1),
                p_3 = calc_callbacks[r-2](n_2 + ((r > 2)?1:0));
          return {x: (p_1.x + p_2.x - p_3.x), y: (p_1.y + p_2.y - p_3.y)};
        })
      }
      const sample_pont = calc_callbacks[r](0);
      const magnitude = Math.sqrt(sample_pont.x**2 + sample_pont.y**2);

      let current_points : number[][] = [];
      for (let i = 0; i < n; i++) {
        const point = get_point(
          magnitude * Math.min(w,h)*0.5, 
          Math.PI*(2*i/n + ((r % 2 === 0)?0:1/n) + 1/n)
        );
        // ctx.beginPath();
        // ctx.arc(point.x + w * 0.5, point.y + h * 0.5, 1, 0, 2 * Math.PI);
        // ctx.stroke();

        let new_point = {x: point.x, y: point.y};
        // var noise_make = noise(new_point.x / 20, new_point.y / 20, lt * 20);
        // new_point.x *= 1 - noise_make * 0.01;
        // new_point.y *= 1 - noise_make * 0.01;

        current_points.push([new_point.x + w * 0.5, new_point.y + h * 0.5]);
      }
      points.push(current_points);
      ctx.lineWidth = 2;
      // ctx.strokeStyle = waveColors[r % waveColors.length];
      ctx.strokeStyle = "#FFFFFF";
      // console.log("points", points.length)
      if (r > 0) {

        for (let i = 0; i < n; i++) {
          const wrapped_i = (i+((r%2===0)?(-1):(1)));
          const next_point_i = (wrapped_i < 0)?((wrapped_i + n) % n):(wrapped_i % n);
          ctx.beginPath();
          ctx.moveTo(points[r][i][0], points[r][i][1]);
          // ctx.lineTo(points[r][next_point_i][0], points[r][next_point_i][1]);
          // ctx.lineTo(points[r-1][next_point_i][0], points[r-1][next_point_i][1]);
          // ctx.lineTo(points[r][i][0], points[r][i][1]);
          if (r === R_COUNT - 1) {
            ctx.lineTo(points[r][next_point_i][0], points[r][next_point_i][1]);
            ctx.lineTo(points[r-1][next_point_i][0], points[r-1][next_point_i][1]);
            ctx.lineTo(points[r][i][0], points[r][i][1]);
          } else {
            ctx.lineTo(points[r-1][next_point_i][0], points[r-1][next_point_i][1]);
            // ctx.lineTo(points[r][i][0], points[r][i][1]);
            ctx.lineTo(points[r][i][0], points[r][i][1]);
            ctx.lineTo(points[r-1][i][0], points[r-1][i][1]);
          }

          // const next_point = points[r-1][next_point_i];
          // console.log("next_point", next_point);
          // ctx.moveTo(points[r][i][0], points[r][i][1]);
          // ctx.lineTo(next_point[0], next_point[1]);
          // ctx.lineTo(points[r][i][0], points[r][i][1]);
          
          ctx.closePath();
          // if (r === 7) {

          //   // if (i % 2 === 1)
          //   ctx.fillStyle = "#FFFFFF";
          //   ctx.fill();
          // }
          // console.log("next_point", next_point)
          // ctx.lineTo(points[r-1][(i-1)%points[r-1].length][0], points[r-1][(i-1)%points[r-1].length][1]);
          // ctx.lineTo(points[r-1][(i-1)%n][0], points[r-1][(i-1)%n][1]);
          ctx.stroke();
        }
      }

    }

    // for (i = 0; i < n; i++) {
    //   const lt = speedSet[i] * 0.001 * time_passed * 0.05;
    //   ctx.beginPath();
    //   ctx.lineWidth = waveWidth || 50;
    //   ctx.strokeStyle = waveColors[i % waveColors.length];
      
      
    //   // Define the control points for the Bezier curve
    //   const controlPoints = [];
    //   const canvasHeight = canvasRef.current?.height || 100;
    //   for (x = 0; x < w; x += interval) {
    //     const xNormalized = (x) / (w); // x normalized to [0, 1]
    //     const expControl = Math.exp(-Math.pow(50 * (xNormalized - 0.5) * wavePinchMiddle, 2));
    //     const pinchedAmplitude = waveAmplitude * canvasHeight * ((1 - wavePinchEnd) * (1 + Math.sin(Math.PI * xNormalized) * expControl + wavePinchEnd));

    //     var y = noise(x, 2 * i, lt) * waveAmplitude * canvasHeight * 0.5 + Math.min(w/2, h/2) - 100;
        
    //     // var y = noise(x / 800, 2 * i, lt) * waveAmplitude * canvasHeight + 2;
    //     // controlPoints.push({ x, y: y + h * 0.5 });

    //     var x_from_polar = Math.cos(xNormalized * 2 * Math.PI) * y + w / 2;
    //     var y_from_polar = Math.sin(xNormalized * 2 * Math.PI) * y + h / 2;
    //     controlPoints.push({ x: x_from_polar, y: y_from_polar });
    //   }

    //   // Add a single point at the end of w
    //   const xEnd = w;
    //   const xNormalizedEnd = xEnd / w;
    //   const pinchedAmplitudeEnd = waveAmplitude * ((1 - wavePinchEnd) * Math.sin(Math.PI * xNormalizedEnd) + wavePinchEnd);
    //   const yEnd = noise(xEnd / 800, 2 * i, lt) * pinchedAmplitudeEnd;
    //   // controlPoints.push({ x: xEnd, y: yEnd + h * 0.5 });
    //   // controlPoints.push({ x: w, y: h / 2 });
    //   controlPoints.push(controlPoints[0]);
    //   controlPoints.push(controlPoints[0]);
  
    //   // Draw the Bezier curve
    //   ctx.moveTo(controlPoints[0].x, controlPoints[0].y);
    //   let j;
    //   for (j = 0; j < controlPoints.length - 2; j++) {
    //     ctx.strokeStyle = `rgba(${waveColors[i % waveColors.length]}, ${1 - j / blur})`;
    //     const xc = (controlPoints[j].x + controlPoints[j + 1].x) / 2;
    //     const yc = (controlPoints[j].y + controlPoints[j + 1].y) / 2;
    //     ctx.quadraticCurveTo(controlPoints[j].x, controlPoints[j].y, xc, yc);
    //   }
    //   // curve through the last two points
    //   ctx.quadraticCurveTo(controlPoints[j].x, controlPoints[j].y, controlPoints[j+1].x,controlPoints[j+1].y);
    //   ctx.stroke();
    //   ctx.closePath();
    // }
  };

  let animationId: number;
  const FPS = 60; // Set a target frame rate (e.g., 30 FPS)
  let lastRenderTime = Date.now();

  const render = () => {
    const currentTime = Date.now();
    const timeSinceLastRender = currentTime - lastRenderTime;

    if (timeSinceLastRender > 1000 / FPS) { // Only render if enough time has passed
      ctx.fillStyle = backgroundFill || "white";
      ctx.globalAlpha = waveOpacity || 0.5;
      ctx.fillRect(0, 0, w, h);
      drawWave(waveCount);
      lastRenderTime = currentTime;
    }
    // ctx.drawImage();

    animationId = requestAnimationFrame(render);
  };

  useEffect(() => {
    init();
    return () => {
      cancelAnimationFrame(animationId);
    };
  }, []);

  const [isSafari, setIsSafari] = useState(false);
  useEffect(() => {
    // I'm sorry but i have got to support it on safari.
    setIsSafari(
      typeof window !== "undefined" &&
        navigator.userAgent.includes("Safari") &&
        !navigator.userAgent.includes("Chrome")
    );
  }, []);

  return (
    <div
      className={cn(
        "rounded-md bg-neutral-950 relative flex flex-col items-center justify-center antialiased",
        containerClassName
      )}
    >
      <canvas
        className={cn(
          "transform-gpu absolute inset-0 z-0 bg-inherit h-inherit w-screen",
          // `blur-[${blur}px]`,
          canvasClassName
        )}
        ref={canvasRef}
        id="canvas"
        style={{
          willChange: 'transform', // Hint the browser for GPU acceleration
          // ...(isSafari ? { filter: `blur(${blur}px)` } : {}),
        }}
      ></canvas>
      <div className={cn("relative z-10", className)} {...props}>
        {children}
      </div>
    </div>
  );
};


export const create_logo_svg = () => {
  // time_passed = Date.now() - start_time;
  const n = 8;
  const r_count = 5;

  let points : number[][][] = [];
  const calc_callbacks = [(n_2 : number) => get_point(waveAmplitude, Math.PI*(2*n_2/n + 1/n))]
  // const lt = 0.001 * time_passed * 0.05;
  const waveAmplitude = 100, h = 600, w = 300;

  let paths : number[][] = [];
  let polygons : number[][] = [];

  for (let r = 0; r < r_count; r++){
    
    if (r === 1) {
      calc_callbacks.push((n_2 : number) => {
        return get_point(waveAmplitude*Math.cos(Math.PI/n), Math.PI*(2*n_2/n));
      })
    } else if (r > 1) {
      calc_callbacks.push((n_2 : number) => {
        const p_1 = calc_callbacks[r-1](n_2),
              p_2 = calc_callbacks[r-1](n_2 + 1),
              p_3 = calc_callbacks[r-2](n_2 + ((r > 2)?1:0));
        return {x: (p_1.x + p_2.x - p_3.x), y: (p_1.y + p_2.y - p_3.y)};
      })
    }
    const sample_pont = calc_callbacks[r](0);
    const magnitude = Math.sqrt(sample_pont.x**2 + sample_pont.y**2);

    let current_points : number[][] = [];
    for (let i = 0; i < n; i++) {
      const point = get_point(
        magnitude * Math.min(w,h)*0.5 / 100, 
        Math.PI*(2*i/n + ((r % 2 === 0)?0:1/n) + 1/n)
      );
      // ctx.beginPath();
      // ctx.arc(point.x + w * 0.5, point.y + h * 0.5, 1, 0, 2 * Math.PI);
      // ctx.stroke();

      let new_point = {x: point.x, y: point.y};
      // var noise_make = noise(new_point.x / 20, new_point.y / 20, lt * 20);
      // new_point.x *= 1 - noise_make * 0.01;
      // new_point.y *= 1 - noise_make * 0.01;

      current_points.push([new_point.x + w * 0.5, new_point.y + h * 0.5]);
    }
    points.push(current_points);
    // ctx.lineWidth = 2;
    // ctx.strokeStyle = waveColors[r % waveColors.length];
    // ctx.strokeStyle = "#FFFFFF";
    // console.log("points", points.length)
    if (r >= 2) {

      for (let i = 0; i < n; i++) {
        const wrapped_i = (i+((r%2===0)?(-1):(1)));
        const next_point_i = (wrapped_i < 0)?((wrapped_i + n) % n):(wrapped_i % n);
        if (r === r_count - 1) {
          paths.push([points[r][i][0], points[r][i][1], points[r][next_point_i][0], points[r][next_point_i][1]])
          paths.push([points[r][next_point_i][0], points[r][next_point_i][1], points[r-1][next_point_i][0], points[r-1][next_point_i][1]]);
          paths.push([points[r-1][next_point_i][0], points[r-1][next_point_i][1], points[r][i][0], points[r][i][1]]);
          polygons.push([
            points[r][i][0], 
            points[r][i][1], 
            points[r][next_point_i][0], 
            points[r][next_point_i][1], 
            points[r-1][next_point_i][0], 
            points[r-1][next_point_i][1],
            points[r][i][0], 
            points[r][i][1],
          ])
        } else {
          paths.push([points[r][i][0], points[r][i][1], points[r-1][next_point_i][0], points[r-1][next_point_i][1]]);
          paths.push([points[r-1][next_point_i][0], points[r-1][next_point_i][1], points[r][i][0], points[r][i][1]]);
          paths.push([points[r][i][0], points[r][i][1], points[r-1][i][0], points[r-1][i][1]]);
        }
        polygons.push([
                        points[r][i][0], 
                        points[r][i][1], 
                        points[r-1][next_point_i][0], 
                        points[r-1][next_point_i][1],
                        points[r-2][i][0], 
                        points[r-2][i][1], 
                        points[r-1][i][0], 
                        points[r-1][i][1],
                        points[r][i][0], 
                        points[r][i][1], 
                      ])
        
      }
    }

  }

  let svgString = '<svg xmlns="http://www.w3.org/2000/svg">';

  // paths.forEach(path => {
  //   svgString += `<line x1="${path[0]}" y1="${path[1]}" x2="${path[2]}" y2="${path[3]}" stroke="black" />`;
  //   svgString += `<line x1="${path[0]}" y1="${path[1]}" x2="${path[2]}" y2="${path[3]}" stroke="black" />`;
  // });

  const SCALE_FACTOR = 0.9;

  polygons.forEach(polygon => {
    const point_pairs : string[] = [];
    let x_points : number[] = [], 
        y_points : number[] = [],
        x_avg : number = 0,
        y_avg : number = 0;

    for (let i = 0; i + 1 < polygon.length; i+=2) {
      x_points.push(polygon[i]);
      y_points.push(polygon[i+1]);
      x_avg += polygon[i];
      y_avg += polygon[i+1];
      // point_pairs.push(`${polygon[i]} ${polygon[i+1]}`);
    }

    x_avg /= x_points.length;
    y_avg /= y_points.length;

    
    for (let i = 0; i + 1 < polygon.length; i += 2) {
      const x_diff = x_points[i/2] - x_avg;
      const y_diff = y_points[i/2] - y_avg;
      x_points[i/2] = x_avg + x_diff * SCALE_FACTOR;
      y_points[i/2] = y_avg + y_diff * SCALE_FACTOR;
      point_pairs.push(`${x_points[i/2]} ${y_points[i/2]}`);
    }
    point_pairs.push(`${x_points[0]} ${y_points[0]}`);

    // for (let i = 0; i + 1 < polygon.length; i+=2) {
    //   x_points.push(polygon[i]);
    //   y_points.push(polygon[i+1]);
    //   point_pairs.push(`${polygon[i]} ${polygon[i+1]}`);
    // }
    svgString += `<polygon points="${point_pairs.join(" ")}" fill="black" />`;
  });



  svgString += '</svg>';

  console.log("Created SVG")
  console.log(svgString);

};

export const QueryLakeLogoSvg = ({
  className = ""
}:{
  className?: string
}) => (
  <svg className={cn("subpixel-antialiased", className)} fill="currentColor" xmlns="http://www.w3.org/2000/svg" width="580.0005" height="580.0003" viewBox="0 0 580.0005 580.0003">
    <g>
      <path d="m474.6506,473.0248c-1.0491,1.0356-1.5764,1.5969-.8026.8232.2718-.2718.5323-.5505.8026-.8232Z"/>
      <path d="m504.0015,502.4803c-24.1063,24.1063-51.8405,43.2878-82.5459,57.16h139.7708v-139.8502c-13.8772,30.7627-33.0809,58.5462-57.2249,82.6902h0Z"/>
    </g>
    <path d="m294.8662,30.0002c65.7792,0,131.156,24.7444,180.7728,74.3612,100.4729,100.4727,98.9358,265.4896-3.426,367.8516-51.8118,51.8117-119.6573,77.7872-187.0787,77.7872-65.7792,0-131.1558-24.7442-180.7729-74.3613C3.8889,375.1667,5.4259,210.1491,107.7875,107.7875c51.812-51.812,119.6572-77.7874,187.0787-77.7874m0-30.0001c-38.1177,0-75.3636,7.2934-110.7029,21.6779-36.5843,14.891-69.418,36.7253-97.589,64.8964-27.8284,27.8283-49.4847,60.2294-64.3674,96.3034C7.8308,217.7237.3638,254.4855.0129,292.1424c-.3511,37.7108,6.4516,74.4163,20.2191,109.0969,14.2833,35.9794,35.4513,68.1483,62.9161,95.613,27.127,27.127,58.8656,48.1223,94.3341,62.4027,34.1894,13.7656,70.4089,20.7453,107.6519,20.7453,38.1176,0,75.3634-7.2935,110.703-21.6779,36.5843-14.891,69.4178-36.7253,97.5889-64.8962,27.8286-27.8286,49.4849-60.2298,64.3676-96.3037,14.3762-34.8459,21.8433-71.6077,22.194-109.2644.3513-37.7109-6.4516-74.4164-20.2193-109.0969-14.2833-35.9794-35.4514-68.1483-62.9163-95.6132-27.1269-27.1269-58.8654-48.1223-94.334-62.4027C368.3285,6.9798,332.1092,0,294.8662,0h0Z"/>
    <g>
      <g id="L3">
        <path d="m121.9639,202.5741l244.5321,244.5322c3.583,3.583,5.4038,7.4033,4.8706,10.2192-.5311,2.8049-3.4884,5.5701-8.1139,7.5866-2.2068.9622-4.4631,1.8965-6.7062,2.7769-22.7592,8.9336-46.6722,13.4633-71.0745,13.4633l-.3947-.0005c-50.1375-.1003-96.9845-19.3907-131.9114-54.3175-34.9267-34.9268-54.217-81.7738-54.3173-131.9111-.0492-24.5403,4.4804-48.5862,13.4628-71.4695,2.7993-7.1318,6.031-14.1201,9.6523-20.8796m-1.9338-24.6705c-3.3229,0-6.6135,1.6396-8.5331,4.763-6.6008,10.7402-12.2433,22.0532-16.8717,33.8449-9.8589,25.1164-14.8304,51.5107-14.7765,78.4497.1105,55.1981,21.3771,106.8028,59.8823,145.3081,38.5055,38.5053,90.1102,59.772,145.3083,59.8825.1431.0003.2897.0004.4327.0004,26.7902,0,53.0338-4.9705,78.0168-14.777,2.4738-.971,4.9266-1.9867,7.3575-3.0465,22.0724-9.623,26.1111-31.6313,9.0847-48.6576L127.0946,180.8347c-1.9771-1.9771-4.5303-2.9312-7.0645-2.9312h-.0002Z"/>
      </g>
      <g id="L1">
        <path d="m117.1033,152.8655c.4068,0,.6049.1981.7001.2932l292.3305,292.3305c5.2543,5.2544,7.7862,11.383,7.1292,17.2567-.6647,5.9429-4.5459,11.4323-10.9285,15.4572-36.2576,22.8639-78.054,34.9491-120.8706,34.9491-58.8337,0-113.854-22.619-154.9254-63.6904-38.4676-38.4677-61.0068-89.9155-63.4655-144.8663-2.4453-54.6529,15.0366-108.4021,49.2255-151.3464.0835-.1049.3054-.3836.8047-.3836m0-19c-5.8581,0-11.6898,2.5511-15.6693,7.5496-76.1973,95.7107-71.2709,234.5412,15.6696,321.4817,46.211,46.211,107.0972,69.2554,168.3604,69.2554,45.3925,0,90.9849-12.6412,131.0052-37.8777,23.405-14.7591,26.6653-42.6547,7.0997-62.2203L131.2384,139.7237c-3.9281-3.9281-9.0417-5.8582-14.1351-5.8582h0Z"/>
      </g>
    </g>
    <g>
      <g id="L3-2">
        <path d="m296.2364,100.5568h0l.3954.0005c50.1374.1003,96.9843,19.3906,131.9111,54.3174,34.9268,34.9269,54.2172,81.7738,54.3175,131.9112.0491,24.5401-4.4804,48.5858-13.4628,71.4691-.8809,2.2444-1.8152,4.5007-2.777,6.7068-1.0761,2.4682-4.0702,8.2088-8.6216,8.2088-2.6807,0-6.0283-1.81-9.1842-4.9659L204.2827,123.6724c6.7594-3.6214,13.7475-6.8529,20.8797-9.6524,22.7587-8.9335,46.6715-13.4631,71.074-13.4632m0-19c-26.7885,0-53.0348,4.971-78.0163,14.7769-11.7917,4.6286-23.1047,10.2709-33.8449,16.8718-5.5054,3.3835-6.4013,11.0282-1.8318,15.5975l252.8365,252.8364c7.0946,7.0947,15.051,10.5309,22.6192,10.5309,10.5945,0,20.4251-6.7404,26.0384-19.6156,1.0598-2.4308,2.0755-4.8835,3.0466-7.3575,9.8588-25.1164,14.8304-51.5106,14.7765-78.4496-.1105-55.1981-21.3772-106.8028-59.8825-145.3082-38.5053-38.5053-90.11-59.7719-145.3081-59.8824-.1447-.0003-.2888-.0004-.4335-.0004h0v.0002Z"/>
      </g>
      <g id="L1-2">
        <path d="m296.2617,68.5568c58.823,0,113.8372,22.619,154.9086,63.6903,18.0915,18.0916,32.6855,38.9663,43.3765,62.0441,10.3402,22.3205,16.8145,46.1964,19.2433,70.9645,4.8739,49.7038-7.1577,100.4134-33.8785,142.7874-4.4861,7.1141-10.6358,11.032-17.3162,11.032-5.3416,0-10.666-2.501-15.3977-7.2327L154.8672,119.5119c-.0948-.0948-.3168-.3168-.2913-.7666.0257-.4548.2752-.6534.3817-.7382,20.3125-16.1712,43.017-28.6455,67.4829-37.0763,23.8225-8.2091,48.6543-12.3723,73.8176-12.374h.0036m-.0168-19c-53.9861.0037-108.292,17.8961-153.1213,53.5857-9.3446,7.4394-10.1373,21.3585-1.6914,29.8044l292.3305,292.3305c8.6089,8.6089,18.827,12.7977,28.8327,12.7977,12.7344,0,25.1225-6.7906,33.3876-19.8974,59.2967-94.0331,49.0729-218.9149-31.3777-299.3656-46.219-46.219-107.0861-69.2595-168.3604-69.2553h0Z"/>
      </g>
    </g>
  </svg>
);