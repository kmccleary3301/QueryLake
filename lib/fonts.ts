// import { JetBrains_Mono as FontMono, Inter as FontSans } from "next/font/google"
import { JetBrains_Mono as FontMono } from "next/font/google"
// import { GeistMono } from "geist/font/mono"
import { GeistSans } from "geist/font/sans"
import localFont from 'next/font/local'



// export const fontSans = FontSans({
//   subsets: ["latin"],
//   variable: "--font-sans",
// })





// export const fontSans = GeistSans

export const fontSans = localFont({
  src: [
    {
      path: '../assets/fonts/Geist/Geist-Regular.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../assets/fonts/Geist/Geist-Bold.woff2',
      weight: '700',
      style: 'normal',
    }
  ],
  variable: "--font-sans",
})

export const fontSoehne = localFont({
  src: [
    {
      path: '../assets/fonts/Soehne/soehne-buch.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../assets/fonts/Soehne/soehne-halbfett.woff2',
      weight: '700',
      style: 'normal',
    }
  ],
  variable: "--font-soehne",
})

export const fontMono = FontMono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export const fontConsolas = localFont({
  src: [
    {
      path: '../assets/fonts/Consolas/Consolas.ttf',
      weight: '400',
      style: 'normal',
    }
  ],
  variable: "--font-consolas",
})
