import React, { useContext , useEffect, useState } from "react";
import { Context } from "../store/appContext";
import shootinGame from "../../img/cod.png";
import "../../styles/home.css";
import rigoImageUrl from "../../img/rigo-baby.jpg";
import { useParams } from "react-router-dom";
import { ReviewModal } from "../component/reviewModal";
import { ReviewCard } from "../component/reviewCard";

export const GamePage = () => {
    const { store, actions } = useContext(Context);
    const { id } = useParams();
    const [game, setGame] = useState(null);
    const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
    const [userInfo, setUserInfo] = useState({});

    const handleReviewModal = () => {
        isReviewModalOpen ? setIsReviewModalOpen(false) : setIsReviewModalOpen(true);
    };

    const fetchGameDetails = async () => {
        const response = await fetch(process.env.BACKEND_URL + 'fetch_game/' + id);
        if (response.ok) {
            const data = await response.json();
            setGame(data);
        }
    };

    useEffect(() => {
        actions.handleFetchUserInfo();
        actions.handleFetchAllReviews();
      }, []);

    useEffect(() => {
        fetchGameDetails();
    }, [id]);

    useEffect(() => {
        setUserInfo(sessionStorage.getItem("userInfo"));
    }, [store.user]);

    if (!game || !store.reviews) {
        return <div>Loading...</div>;
    }

    let a = 0;
    game.rating ? game.rating = (Math.round(game.rating * 100) / 100).toFixed(2) : a = 0;
    let b = 0;
    return (
        <div>
            <div className="gameBanner text-bg-dark my-4">
                <h1 className="text-center">{game.name}</h1>
            </div>
            <div className="row g-0">
                <div className="col-md-4">
                <img src={`//images.igdb.com/igdb/image/upload/t_1080p/${game.cover_id}.jpg`} className="banner-img d-block mx-auto" alt="..." style={{ width: '250px', height: 'auto' }} />
                </div>
                <br></br>
                <div className="col-md-8">
                    <div className="card-body">
                        {game.rating && <p className="card-text">Rating: {game.rating}</p>}
                        <p className="card-text">{game.summary}</p>
                    </div>
                </div>
            </div>
            <div className="row justify-content-center">
                {userInfo && <button onClick={handleReviewModal} type="button" className="btn btn-black mt-4">Review</button>}
                {isReviewModalOpen && <ReviewModal closeModal={handleReviewModal} game={game} />}
            </div>
            <div className="row mt-4 justify-content-center">
                {b > 0 && <h2 className='m-3'>Reviews by users you follow:</h2>}
                {store.reviews.map((review, index) => {
                    if(review.game_id == game.id && store.user.followed.includes(review.username)){
                        b++;
                        return (
                            <ReviewCard key={index} review={review} />
                        );
                    }
                }, [])}
            </div>
            <div className="row justify-content-center">
                {store.reviews[0] &&<h2>Reviews by users:</h2>}
                {store.reviews.map((review, index) => {
                    if(review.game_id == game.id){
                        return (
                            <ReviewCard key={index} review={review} />
                        );
                    }
                }, [])}
            </div>
        </div>
    );
};
