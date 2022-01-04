import React, { createContext, useReducer, useEffect, useContext, useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Landing from "pages/Landing/Index";
import { Provider } from "use-http";
import ConstructionZone from 'pages/ConstructionZone/Index';

function App() {

  const options = {
		headers: {
      "Authorization": "",
      "Content-Type": "application/json"
		},
    cachePolicy: "no-cache"
	}

  return (
      <Provider options={options}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />}/>
            <Route path="/construction_zone" element={<ConstructionZone />}/>
          </Routes>
        </BrowserRouter>
      </Provider>
  );
}

export default App;
