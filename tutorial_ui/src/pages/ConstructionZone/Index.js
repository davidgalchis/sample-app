import space_coder from "images/space_coder.gif"
import "styles/App.scss"
import {useNavigate} from "react-router-dom";
import CloudKommandLogo from "images/cloudkommand_logo.svg"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowLeft, faChevronLeft
} from "@fortawesome/free-solid-svg-icons";


export default function ConstructionZone() {
    const navigate = useNavigate()

    const route_to_x = (path) => {
        navigate(path)
    }

    return (
        <div className="construction_zone">
            <div className="header_bar">
                <img className="header_bar-img" onClick={()=>{route_to_x(`/`)}} src={CloudKommandLogo}/>
            </div>
            <div className="construction_zone_body">
                <div className="title_bar">
                    <div className="title_bar_item">
                        <button className="title_bar_button" onClick={() => navigate(-1)}>                        
                            <FontAwesomeIcon className="title_bar_icon" icon={faArrowLeft} size="2x"/>
                        </button>
                    </div>
                    <div className="title_bar_item_large">
                        <div className="title_bar_text">Click...click...[humming]...sip...click, click...</div>
                    </div>
                    <div className="title_bar_item"></div>
                </div>
                <div className="title_bar_subtext">You've found a construction zone. While we transmute some coffee, feel free to enjoy some of the more finished areas of the app!</div>
                <img className="body_image" src={space_coder}/>
            </div>
        </div>
    );
}