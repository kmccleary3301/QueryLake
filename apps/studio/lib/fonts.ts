import localFont from "next/font/local";

export const fontSans = localFont({
  src: [
    {
      path: "../assets/fonts/Soehne/soehne-buch.woff2",
      weight: "400",
      style: "normal",
    },
    {
      path: "../assets/fonts/Soehne/soehne-halbfett.woff2",
      weight: "600",
      style: "normal",
    },
  ],
  variable: "--font-sans",
  display: "swap",
});

export const fontDisplay = localFont({
  src: [
    {
      path: "../assets/fonts/Soehne/soehne-buch.woff2",
      weight: "400",
      style: "normal",
    },
    {
      path: "../assets/fonts/Soehne/soehne-halbfett.woff2",
      weight: "600",
      style: "normal",
    },
  ],
  variable: "--font-display",
  display: "swap",
});

export const fontMono = localFont({
  src: [
    {
      path: "../assets/fonts/Soehne/soehne-mono-buch.woff2",
      weight: "400",
      style: "normal",
    },
    {
      path: "../assets/fonts/Soehne/soehne-mono-halbfett.woff2",
      weight: "600",
      style: "normal",
    },
  ],
  variable: "--font-mono",
  display: "swap",
});

export const fontConsolas = localFont({
  src: [
    {
      path: "../assets/fonts/Consolas/Consolas.ttf",
      weight: "400",
      style: "normal",
    },
  ],
  variable: "--font-consolas",
  display: "swap",
});

export const fontSoehne = fontSans;

export const fontInter = localFont({
  src: [
    {
      path: "../assets/fonts/Inter/regular.ttf",
      weight: "400",
      style: "normal",
    },
    {
      path: "../assets/fonts/Inter/medium.ttf",
      weight: "500",
      style: "normal",
    },
    {
      path: "../assets/fonts/Inter/semi-bold.ttf",
      weight: "600",
      style: "normal",
    },
  ],
  variable: "--font-inter",
  display: "swap",
});
