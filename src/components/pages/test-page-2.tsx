// import { useState } from 'react'
import '@/App.css'
// import { Button } from './components/ui/button'
import { Button } from '@/components/ui/button'
import craftUrl from '@/hooks/craftUrl'

export default function TestPage2() {

  const attempt_login = () => {
    const url = craftUrl(`/api/login`, {
      "username": "w",
      "password": "w"
    });

    fetch(url, {method: "POST"}).then((response) => {
      console.log("Fetching");
      console.log(response);
      response.json().then((data) => {
        console.log("Got data:", data);
      });
    });
  }

  return (
    <>
      <Button variant="outline" onClick={() => {console.log("Button clicked"); attempt_login();}}>
        <p>
          {"This is a fucking button (Number 2)!"}
        </p>
      </Button>
    </>
  )
}
