import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import ScrollToTop from "./component/scrollToTop";
import { BackendURL } from "./component/backendURL";

import { Demo } from "./pages/demo";

import { GameList } from "./pages/gameList"
import { Single } from "./pages/single";

import { Private } from "./pages/private";
import { Testhome } from "./pages/testhome";

import injectContext from "./store/appContext";
import { Home } from "./pages/home";

import { Navbar } from "./component/navbar";
import { Footer } from "./component/footer";

//create your first component
 const Layout = () => {
    //the basename is used when your project is published in a subdirectory and not in the root of the domain
    // you can set the basename on the .env file located at the root of this project, E.g: BASENAME=/react-hello-webapp/
    const basename = process.env.BASENAME || "";

    if(!process.env.BACKEND_URL || process.env.BACKEND_URL == "") return <BackendURL/ >;

    return (
        <div>
            <BrowserRouter basename={basename}>
                <ScrollToTop>
                    <Navbar />
                    <Routes>
                        <Route element={<Home />} path="/" />
                        <Route element={<Demo />} path="/demo" />
                        <Route element={<Private />} path="/private" />
                        <Route element={<Testhome />} path="/testhome" />
                        <Route element={<h1>Not found!</h1>} />
                        <Route element={<GameList />} path="/gamelist" />
                    </Routes>
                    <Footer />
                </ScrollToTop>
            </BrowserRouter>
        </div>
    );
};

export default injectContext(Layout);
