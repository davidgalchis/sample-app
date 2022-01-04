import React, { useContext, useEffect, useState } from "react";
import { Link, Redirect, useNavigate } from "react-router-dom";
import "styles/App.scss";
import CloudKommandLogo from "images/cloudkommand_logo.svg"
import CloudKommandLogoDark from "images/cloudkommand_logo_dark.svg"
import DiscordLogo from "images/discord-brands.svg"
import PatternL from "images/pattern-l.svg"
import CompleteDeploymentScreenshot from "images/deployment_screenshot.png"
import {useWindowDimensions} from "helpers/util"
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faArrowRight,
  faBars, faCircle, faEllipsisH, faEllipsisV, faTicketAlt, faTimes
} from "@fortawesome/free-solid-svg-icons";
import { get_config } from 'config/config.js'
import useFetch from 'use-http'
import AceEditor from 'react-ace';
import 'brace/mode/json';
import 'brace/theme/vibrant_ink';
import 'brace/theme/dracula';


const BACKEND_API_BASE_URL = get_config().backend_api_endpoint + "/api/v1"
const CLOUDKOMMAND_API_URL = get_config().cloudkommand_api + "/api/v1"
const CLOUDKOMMAND_DOCUMENTATION_URL = get_config().cloudkommand_url + "/documentation"
const CLOUDKOMMAND_LANDING_PAGE_URL = get_config().cloudkommand_url
const DISCORD_CHANNEL_URL = get_config().discord_channel_url

const demo_text = `{
    "components": {
        "tutorial_table": {
            "type": "@dynamodb.table"
        },
        "tutorial_api": {
            "type": "@apigateway.api",
            "resources": {
                "/{proxy+}": {
                    "ANY": "@tutorial_lambda:props.arn"
                }
            },
            "cors_enabled": true
        },
        "tutorial_lambda": {
            "type": "@lambda.function",
            "description": "CloudKommand Tutorial Lambda",
            "timeout": 10,
            "policies": ["@tutorial_policy"],
            "environment_variables": {
                "table_name": "@tutorial_table:props.name"
            }
        },
        "tutorial_policy": {
            "type": "@iam.policy",
            "description": "CloudKommand Tutorial Policy",
            "document": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "Vis",
                    "Effect": "Allow",
                    "Action": [
                        "lambda:*",
                        "events:*",
                        "dynamodb:*",
                        "sns:*"
                    ],
                    "Resource": "*"
                }]
            }
        }
    },
    "repos": {
        "iam": "https://github.com/cloudkommand/iam",
        "lambda": "https://github.com/cloudkommand/lambda",
        "dynamodb": "https://github.com/cloudkommand/dynamodb",
        "apigateway": "https://github.com/cloudkommand/apigateway"
    }
}`

export function GeneralHeader({loggedIn}) {
  const { height, width } = useWindowDimensions()
  const navigate = useNavigate()
  const route_to_x = (path) => {
    navigate(path)
  }
  return (
    <div className="landing_page__header">
        <img className="landing_page__header-img" onClick={()=>{window.open(CLOUDKOMMAND_LANDING_PAGE_URL, "_blank")}} src={CloudKommandLogo}/>
        <div className="landing_page__header-navbar">
          {
            width > 940 ?
            <>
              <a className="landing_page__header-navbar-navitem" onClick={()=>{window.open(CLOUDKOMMAND_DOCUMENTATION_URL, "_blank")}}><img className="landing_page__header-smallimg" src={CloudKommandLogo}/>Usage Guide</a>
              <a className="landing_page__header-navbar-navitem" onClick={()=>{window.open(DISCORD_CHANNEL_URL, "_blank")}}><img className="landing_page__header-smallimg" src={CloudKommandLogo}/>Q & A</a>
              <a className="landing_page__header-navbar-navitembtn" onClick={()=>{window.open(CLOUDKOMMAND_LANDING_PAGE_URL, "_blank")}}>Back to <img className="landing_page__header-smallimg" src={CloudKommandLogoDark}/></a>
            </>
            : width > 500 ?
            <>
              <div style={{"float":"left"}}>
              <a className="landing_page__header-navbar-navitembtn" href="/login">Back to <img className="landing_page__header-smallimg" src={CloudKommandLogoDark}/></a>
              </div>
              <div style={{"float":"right"}}>
                <div className="landing_page__header-navbar-dropdown">
                  <button className="landing_page__header-navbar-dropbtn">
                    <i><FontAwesomeIcon icon={faBars} size="lg" /></i>
                  </button>
                  <div className="landing_page__header-navbar-dropbtn-base"></div>
                  <div className="landing_page__header-navbar-dropdown-content">
                    <a className="landing_page__header-navbar-dropdown-content-a" onClick={()=>{window.open(CLOUDKOMMAND_DOCUMENTATION_URL, "_blank")}}><span className="landing_page__header-navbar-dropdown-pill"></span><img className="landing_page__header-smallimg" src={CloudKommandLogo}/>Usage Guide</a>
                    <a className="landing_page__header-navbar-dropdown-content-a" onClick={()=>{window.open(DISCORD_CHANNEL_URL, "_blank")}}><span className="landing_page__header-navbar-dropdown-pill"></span><img className="landing_page__header-smallimg" src={CloudKommandLogo}/>Q & A</a>
                  </div>
                </div>
              </div>
            </>
            : <div className="landing_page__header-navbar-dropdown">
              <button className="landing_page__header-navbar-dropbtn">
                <i><FontAwesomeIcon icon={faBars} size="lg" /></i>
              </button>
              <div className="landing_page__header-navbar-dropbtn-base"></div>
              <div className="landing_page__header-navbar-dropdown-content">
                <a className="landing_page__header-navbar-dropdown-content-a" onClick={()=>{window.open(CLOUDKOMMAND_DOCUMENTATION_URL, "_blank")}}><span className="landing_page__header-navbar-dropdown-pill"></span><img className="landing_page__header-smallimg" src={CloudKommandLogo}/>Usage Guide</a>
                <a className="landing_page__header-navbar-dropdown-content-a" onClick={()=>{window.open(DISCORD_CHANNEL_URL, "_blank")}}><span className="landing_page__header-navbar-dropdown-pill"></span><img className="landing_page__header-smallimg" src={CloudKommandLogo}/>Q & A</a>
                <a className="landing_page__header-navbar-navitembtn" onClick={()=>{window.open(CLOUDKOMMAND_LANDING_PAGE_URL, "_blank")}}>Back to<img className="landing_page__header-smallimg" src={CloudKommandLogoDark}/></a>
              </div>
            </div>
          }
        </div>
      </div>
  )
};

export function GeneralFooter() {
  const navigate = useNavigate()
  const route_to_x = (path) => {
    navigate(path)
  }
  return (
    <div className="landing_page__footer" >
      <body>
        <div class="container"></div>
        <footer>
          <section class="ft-main">
            <div class="ft-main-item">
              <img className="ft-main-item-img" onClick={()=>{window.open(CLOUDKOMMAND_LANDING_PAGE_URL, "_blank")}} src={CloudKommandLogo}/>
            </div>
            <div class="ft-main-item">
              <h2 class="ft-title">About</h2>
              <ul>
                <li><a><i>Coming Soon!</i></a></li>
              </ul>
            </div>
            <div class="ft-main-item">
              <h2 class="ft-title">Product</h2>
              <ul>
                <li><a><i>Coming Soon!</i></a></li>
              </ul>
            </div>
            <div class="ft-main-item">
              <h2 class="ft-title">Follow Us</h2>
              <ul>
                <li>
                  <a className="ft-follow-row-spacing" onClick={()=>{window.open(DISCORD_CHANNEL_URL, "_blank")}}><img className="ft-follow-row" src={DiscordLogo}/></a>
                </li>
              </ul>
            </div>
          </section>
        
          <section class="ft-legal">
            <ul class="ft-legal-list">
              <li><a onClick={()=>{route_to_x(`/construction_zone`)}}>Privacy</a></li>
              <li><a onClick={()=>{route_to_x(`/construction_zone`)}}>Terms</a></li>
              <li>&copy; 2021 CloudKommand</li>
            </ul>
          </section>
        </footer>
      </body>
    </div>
  )
};

function CloudKommandExtensionSection () {
    const { get, post, response, loading, error } = useFetch(`${CLOUDKOMMAND_API_URL}`)
    const [ extensionsDeployed, setExtensionsDeployed ] = useState(null)

    async function callExtensionsDeployedCounter() {
        const extensions_deployed_response = await get(`/metrics/extensions`)
        if (response.ok) setExtensionsDeployed(extensions_deployed_response)
    }

    useEffect(()=>{
        callExtensionsDeployedCounter()
    },[])
  
    console.log(extensionsDeployed)
    return <div className="body_first_section_content_column_extensions_deployed_counter">{extensionsDeployed ? extensionsDeployed.the_count.toLocaleString(navigator.language, { minimumFractionDigits: 0 }) : ""}</div>
}

export default function Landing() {
    
    const navigate = useNavigate();
    const { height, width } = useWindowDimensions()

    const { get, post, response, loading, error } = useFetch(`${BACKEND_API_BASE_URL}`)

    const [ clickCounter, setClickCounter ] = useState(null)

    async function callClickCounter() {
        const click_counter_response = await get(`/click_counter`)
        if (response.ok) setClickCounter(click_counter_response)
    }

    useEffect(()=>{
        callClickCounter()
    },[])
  
    console.log(clickCounter)

    return (
        <div className="landing_page">
        <GeneralHeader />
        <div className="section_dark">
            {width > 700
            ? <>
                <img className="left_image_pattern" src={PatternL}/>
                <img className="right_image_pattern" src={PatternL}/>
            </>
            :<></>
            }
            <div className="body_first">
              <div className="container">
                  <div className="bd_intro_container">
                  <div className="bd_intro_container_items_headliner" >
                      <div className="bd_intro_container_items_headliner_item">
                        <img className="bd_intro_container_items_headliner_image" onClick={()=>{navigate("/")}} src={CloudKommandLogo}/>
                        <div className="bd_intro_container_items_headliner_inner_text">CloudKommand</div>
                      </div>
                      <div className="bd_intro_container_items_headliner_item">
                        <div className="bd_intro_container_items_headliner_inner_text">Sample UI</div>
                      </div>
                  </div>
                  <div className="body_first_section_content">
                    <div className="body_first_section_content_column">
                      {/* <div className="body_first_section_content_column_header_container">
                        <div className="body_first_section_content_column_header_items">
                        <div className="body_first_section_content_column_header_additional_text">Talk to your API!</div>
                        </div>
                      </div> */}
                      <div className="body_first_section_content_column_header_title"><span className="bright">Try out your live API now!</span></div>
                      <div className="body_first_section_content_column_ping_button" onClick={callClickCounter}>Ping Your API</div>
                      <div className="body_first_section_content_column_api_ping_counter">Times API Pinged: &nbsp;<span className="bright">{`${clickCounter ? clickCounter.click_counter : ""}`}</span></div>
                    </div>
                    <div className="landing_overview_horizontal_divider"></div>
                    <div className="body_first_section_content_column">
                      <div className="body_first_section_content_column_header_container">
                        <div className="body_first_section_content_column_header_title"><span className="bright">Did you know?</span></div>
                        <div className="body_first_section_content_column_header_items">
                          <div className="body_first_section_content_column_header_additional_text"><span className="emphasis">The # of extensions users deployed with</span></div>
                          <div className="body_first_section_header_logo_item">
                            <img className="body_first_section_content_column_header_logo"onClick={()=>{navigate("/")}} src={CloudKommandLogo}/>
                            <div className="body_first_section_content_column_header_items_logo_text">CloudKommand <span className="emphasis">:</span></div>
                          </div>
                        </div>
                      </div>
                      <div><CloudKommandExtensionSection /></div>
                    </div>
                  </div>

                  {/* <div className="bd_intro_container_items_extra_emphasis"><span className="emphasis">Effortless deployments.</span></div>
                  <div className={width < 1000 ? "bd_intro_container_items_container_column": "bd_intro_container_items_container_row"}>
                      <div className="bd_intro_container_items">Managed infrastructure.</div>
                      <div className="bd_intro_container_items">Always free.</div>
                      <div className="bd_intro_container_items">Deploy your first app in 5 minutes.</div>
                      <CloudKommandExtensionSection />
                  </div>
                  <div className="bd_intro_container_items_button" onClick={()=>{navigate("/login")}}>
                      Get Started Now &nbsp;
                      <FontAwesomeIcon icon={faArrowRight} />
                  </div> */}
                  {/* <div className="bd-video-wrapper">
                      <iframe className="bd-video-content" frameborder="0" allowfullscreen="allowfullscreen"
                      src="https://www.youtube.com/embed/jqckyGTAdiY?start=0&autoplay=1&mute=1&loop=1?controls=1">
                      </iframe>
                  </div> */}
                  </div>
              </div>
            </div>
        </div>
        <div className="section_dark">
            <div className="body_first">
            <div className="container">
                <div className="landing_overview_horizontal_divider"></div>
                <div className="landing_overview_headliner_container">
                  <div className="landing_overview_headliner_container_items" >
                    <div className="landing_overview_headliner_container_item_set">
                      <div className="landing_overview_headliner_items_inner_text_secondary">More About</div>
                    </div>
                    <div className="landing_overview_headliner_container_item_set">
                      <img className="landing_overview_headliner_items_image" onClick={()=>{navigate("/")}} src={CloudKommandLogo}/>
                      <div className="landing_overview_headliner_items_inner_text">CloudKommand</div>
                    </div>
                  </div>
                </div>
                <div className={width > 990 ? "landing_overview_content_row" : "landing_overview_content_row_flip"}>
                  <div className={width > 990 ? "landing_overview_content_row_item" : "landing_overview_content_row_item_flip"}>
                      <div className="landing_overview_content_header">Develop</div>
                      <div className="landing_overview_content_first_line">Use our powerful Extensions to whisk away infrastructure code.</div>
                      <div className="landing_overview_content_second_description">Declare full-blown apps and their relationships through simple abstract syntax in JSON.</div>
                      <div className="landing_overview_content_first_line">Develop directly against the cloud. </div>
                      <div className="landing_overview_content_second_description">Easy configuration, managed deployment, and infrastructure sandboxing means developers can now test all their ideas in the cloud instead of praying they work when finally deployed.</div>
                      <div className="landing_overview_content_first_line">Extend your use-cases and workflow with Extensions. </div>
                      <div className="landing_overview_content_second_description">Use our rapidly growing open-source library of powerful Extensions. Or contribute to the community by easily rolling your own!</div>
                  </div>
                  <div className={width > 990 ? "landing_overview_content_row_item" : "landing_overview_content_row_item_flip"}>
                      <AceEditor
                      placeholder="Edit your component json here"
                      mode="json"
                      name="definition_edits"
                      id="definition_edits"
                      theme="vibrant_ink"
                      value={demo_text || ""}
                      highlightActiveLine={true}
                      width={width > 990? "100%" : width > 760 ? "600px": "400px"}
                      height={width > 990? "500px" : width > 760 ? "600px": "400px"}
                      editorProps={{ $blockScrolling: true }}
                      // focus={true}
                      />
                  </div>
                </div>
                <div className={width > 990 ? "landing_overview_content_row" : "landing_overview_content_row_flip"}>
                  <div className={width > 990 ? "landing_overview_content_row_item" : "landing_overview_content_row_item_flip"}>
                      <img className="deployment_screenshot" src={CompleteDeploymentScreenshot}/>
                  </div>
                  <div className={width > 990 ? "landing_overview_content_row_item" : "landing_overview_content_row_item_flip"}>
                      <div className="landing_overview_content_header">Deploy</div>
                      <div className="landing_overview_content_first_line">FAST deployment.</div>
                      <div className="landing_overview_content_second_description">Automatically managed parallel infrastructure deployment that’s optimized for speed and provides a live log feed of everything that’s happening.</div>
                      <div className="landing_overview_content_first_line">Fully managed deployment.</div>
                      <div className="landing_overview_content_second_description">Infrastructure changes are managed. Deploy-order is managed. Infrastructure clash avoidance is managed. And you deploy with a single click of a button.</div>
                      <div className="landing_overview_content_first_line">View live infrastructure.</div>
                      <div className="landing_overview_content_second_description">We provide links to every piece of infrastructure you deploy. View it in real-time in the cloud or link directly to its live log feed to check in on your app. </div>
                  </div>
                </div>
            </div>
            </div>
        </div>
        <GeneralFooter/>
        </div>
    )
}
