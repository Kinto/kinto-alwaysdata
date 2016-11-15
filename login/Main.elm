port module Main exposing (..)

import Html
import Html.Attributes
import Html.Events
import Http
import Json.Decode as Decode
import Platform
import Time


deployUrl : String
deployUrl =
    "http://192.168.1.97:8888/deploy/"


statusUrl : String
statusUrl =
    "http://192.168.1.97:8888/status/"



-- Model


type Msg
    = EmailChange String
    | PasswordChange String
    | InstallKinto
    | PostDeploy (Result Http.Error String)
    | CheckProgress Time.Time
    | UpdateProgress (Result Http.Error String)
    | EncodedAuth String


type alias Model =
    { email : String
    , password : String
    , deploySuccess : Maybe String
    , error : Maybe String
    , progress : Maybe String
    , encodedAuth : String
    }


init : ( Model, Cmd Msg )
init =
    Model "" "" Nothing Nothing Nothing "" ! []



-- Update


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        EmailChange email ->
            { model | email = email }
                ! [ b64encode <| String.join ":" [ email, model.password ] ]

        PasswordChange password ->
            { model | password = password }
                ! [ b64encode <| String.join ":" [ model.email, password ] ]

        InstallKinto ->
            model ! [ postDeploy model.encodedAuth ]

        PostDeploy (Ok deployed) ->
            { model
                | deploySuccess = Just <| toString deployed
                , error = Nothing
            }
                ! []

        PostDeploy (Err error) ->
            { model
                | error = Just <| toString error
                , deploySuccess = Nothing
            }
                ! []

        CheckProgress _ ->
            model ! [ checkProgress model.encodedAuth ]

        UpdateProgress (Ok progress) ->
            { model | progress = Just progress } ! []

        UpdateProgress (Err error) ->
            { model | error = Just <| toString error } ! []

        EncodedAuth encoded ->
            { model | encodedAuth = encoded } ! []


postDeploy : String -> Cmd Msg
postDeploy basicAuth =
    Http.send PostDeploy <|
        Http.request
            { method = "POST"
            , headers = [ Http.header "Authorization" ("Basic " ++ basicAuth) ]
            , url = deployUrl
            , body = Http.emptyBody
            , expect = Http.expectStringResponse (\{ body } -> Ok body)
            , timeout = Nothing
            , withCredentials = False
            }


checkProgress : String -> Cmd Msg
checkProgress basicAuth =
    Http.send UpdateProgress <|
        Http.request
            { method = "GET"
            , headers = [ Http.header "Authorization" ("Basic " ++ basicAuth) ]
            , url = statusUrl
            , body = Http.emptyBody
            , expect = Http.expectStringResponse (\{ body } -> Ok body)
            , timeout = Nothing
            , withCredentials = False
            }



-- Subscriptions


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ case model.deploySuccess of
            Just success ->
                Time.every (5 * Time.second) CheckProgress

            Nothing ->
                Sub.none
        , encoded EncodedAuth
        ]



-- View


view : Model -> Html.Html Msg
view model =
    let
        body =
            case model.deploySuccess of
                Just success ->
                    viewProgress model

                Nothing ->
                    viewForm model

        error =
            Maybe.withDefault "" model.error
    in
        Html.div
            []
            [ body
            , Html.hr [] []
            , Html.div
                [ Html.Attributes.style [ ( "background-color", "white" ) ] ]
                [ Html.text error ]
            , Html.hr [] []
            , Html.div
                [ Html.Attributes.style [ ( "background-color", "white" ) ] ]
                [ Html.text <| toString model ]
            ]


viewForm : Model -> Html.Html Msg
viewForm model =
    Html.div
        [ Html.Attributes.class "login-holder" ]
        [ Html.h1 [] [ Html.text "Login and deploy Kinto" ]
        , Html.div
            [ Html.Attributes.class "well"
            , Html.Attributes.style [ ( "background-color", "#efefef" ) ]
            ]
            [ Html.div
                [ Html.Attributes.id "div_id_login"
                , Html.Attributes.class "form-group"
                ]
                [ Html.label
                    [ Html.Attributes.for "id_login"
                    , Html.Attributes.class "control-label requiredField"
                    ]
                    [ Html.text "Email" ]
                , Html.div
                    [ Html.Attributes.class "controls" ]
                    [ Html.input
                        [ Html.Attributes.placeholder "Email"
                        , Html.Attributes.class "emailinput form-control"
                        , Html.Attributes.id "id_login"
                        , Html.Attributes.required True
                        , Html.Attributes.placeholder "username@alwaysdata.net"
                        , Html.Attributes.type_ "email"
                        , Html.Events.onInput EmailChange
                        ]
                        []
                    ]
                ]
            , Html.div
                [ Html.Attributes.id "div_id_password"
                , Html.Attributes.class "form-group"
                ]
                [ Html.label
                    [ Html.Attributes.for "id_password"
                    , Html.Attributes.class "control-label requiredField"
                    ]
                    [ Html.text "Password" ]
                , Html.div
                    [ Html.Attributes.class "controls" ]
                    [ Html.input
                        [ Html.Attributes.class "textinput textInput form-control"
                        , Html.Attributes.id "id_password"
                        , Html.Attributes.required True
                        , Html.Attributes.type_ "password"
                        , Html.Events.onInput PasswordChange
                        ]
                        []
                    ]
                ]
            ]
        , Html.button
            [ Html.Attributes.type_ "submit"
            , Html.Attributes.class "btn btn-default"
            , Html.Events.onClick InstallKinto
            ]
            [ Html.text "Deploy my kinto!" ]
        , Html.div
            [ Html.Attributes.class "footer-links" ]
            [ Html.a
                [ Html.Attributes.href "https://admin.alwaysdata.com/password/lost/" ]
                [ Html.text "Password forgotten?" ]
            , Html.a
                [ Html.Attributes.href "https://www.alwaysdata.com/signup/"
                , Html.Attributes.class "align-r"
                ]
                [ Html.text "Register" ]
            ]
        ]


viewProgress : Model -> Html.Html Msg
viewProgress model =
    let
        body =
            case model.progress of
                Just progress ->
                    Html.text <| toString progress

                Nothing ->
                    Html.text "Deploying kinto, please wait..."
    in
        Html.div
            [ Html.Attributes.class "login-holder" ]
            [ Html.h1 [] [ Html.text "Currently deploying Kinto" ]
            , Html.div
                [ Html.Attributes.class "well"
                , Html.Attributes.style [ ( "background-color", "#efefef" ) ]
                ]
                [ body ]
            ]



-- Main


main : Program Never Model Msg
main =
    Html.program
        { init = init
        , update = update
        , view = view
        , subscriptions = subscriptions
        }



-- ports


port b64encode : String -> Cmd msg


port encoded : (String -> msg) -> Sub msg
