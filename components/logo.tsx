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
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="272.2931" height="272.2931" viewBox="0 0 272.2931 272.2931">
    <polygon fill="currentColor" points="235.7624 177.4088 272.2931 140.878 272.2931 192.5403 235.7624 229.071 235.7624 177.4088 235.7624 177.4088"/>
    <polygon fill="currentColor" points="177.4088 235.7624 229.071 235.7624 192.5403 272.2931 140.878 272.2931 177.4088 235.7624 177.4088 235.7624"/>
    <polygon fill="currentColor" points="94.8843 235.7624 131.4151 272.2931 79.7528 272.2931 43.2221 235.7624 94.8843 235.7624 94.8843 235.7624"/>
    <polygon fill="currentColor" points="36.5307 177.4088 36.5307 229.071 0 192.5403 0 140.878 36.5307 177.4088 36.5307 177.4088"/>
    <polygon fill="currentColor" points="36.5307 94.8843 0 131.4151 0 79.7528 36.5307 43.2221 36.5307 94.8843 36.5307 94.8843"/>
    <polygon fill="currentColor" points="94.8843 36.5307 43.2221 36.5307 79.7528 0 131.4151 0 94.8843 36.5307 94.8843 36.5307"/>
    <polygon fill="currentColor" points="177.4088 36.5307 140.878 0 192.5403 0 229.071 36.5307 177.4088 36.5307 177.4088 36.5307"/>
    <polygon fill="currentColor" points="235.7624 94.8843 235.7624 43.2221 272.2931 79.7528 272.2931 131.4151 235.7624 94.8843 235.7624 94.8843"/>
    <polygon fill="currentColor" points="179.0324 179.0323 179.0324 230.6946 230.6946 230.6946 230.6946 179.0323 179.0324 179.0323 179.0324 179.0323"/>
    <polygon fill="currentColor" points="136.1465 196.7962 99.6158 233.327 136.1465 269.8577 172.6773 233.327 136.1465 196.7962 136.1465 196.7962"/>
    <polygon fill="currentColor" points="93.2607 179.0323 41.5985 179.0323 41.5985 230.6946 93.2607 230.6946 93.2607 179.0323 93.2607 179.0323"/>
    <polygon fill="currentColor" points="75.4969 136.1465 38.9661 99.6158 2.4354 136.1465 38.9661 172.6773 75.4969 136.1465 75.4969 136.1465"/>
    <polygon fill="currentColor" points="93.2607 93.2607 93.2607 41.5985 41.5985 41.5985 41.5985 93.2607 93.2607 93.2607 93.2607 93.2607"/>
    <polygon fill="currentColor" points="136.1465 75.4969 172.6773 38.9661 136.1465 2.4354 99.6158 38.9661 136.1465 75.4969 136.1465 75.4969"/>
    <polygon fill="currentColor" points="179.0324 93.2607 230.6946 93.2607 230.6946 41.5985 179.0324 41.5985 179.0324 93.2607 179.0324 93.2607"/>
    <polygon fill="currentColor" points="196.7962 136.1465 233.327 172.6773 269.8577 136.1465 233.327 99.6158 196.7962 136.1465 196.7962 136.1465"/>
    <polygon fill="currentColor" points="140.0662 137.7701 191.7285 137.7701 228.2592 174.3009 176.597 174.3009 140.0662 137.7701 140.0662 137.7701"/>
    <polygon fill="currentColor" points="137.7701 140.0662 174.3009 176.597 174.3009 228.2592 137.7701 191.7285 137.7701 140.0662 137.7701 140.0662"/>
    <polygon fill="currentColor" points="134.523 140.0662 134.523 191.7285 97.9922 228.2592 97.9922 176.597 134.523 140.0662 134.523 140.0662"/>
    <polygon fill="currentColor" points="132.2269 137.7701 95.6961 174.3009 44.0339 174.3009 80.5646 137.7701 132.2269 137.7701 132.2269 137.7701"/>
    <polygon fill="currentColor" points="132.2269 134.5229 80.5646 134.5229 44.0339 97.9922 95.6961 97.9922 132.2269 134.5229 132.2269 134.5229"/>
    <polygon fill="currentColor" points="134.523 132.2269 97.9922 95.6961 97.9922 44.0339 134.523 80.5646 134.523 132.2269 134.523 132.2269"/>
    <polygon fill="currentColor" points="137.7701 132.2269 137.7701 80.5646 174.3009 44.0339 174.3009 95.6961 137.7701 132.2269 137.7701 132.2269"/>
    <polygon fill="currentColor" points="140.0662 134.5229 176.597 97.9922 228.2592 97.9922 191.7285 134.5229 140.0662 134.5229 140.0662 134.5229"/>
  </svg>
);