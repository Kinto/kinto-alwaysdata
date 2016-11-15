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
    "https://kinto-ota.dev.mozaws.net/deploy/"


statusUrl : String
statusUrl =
    "https://kinto-ota.dev.mozaws.net/status/"



-- Model


type Msg
    = EmailChange String
    | PasswordChange String
    | InstallKinto
    | PostDeploy (Result Http.Error String)
    | CheckProgress Time.Time
    | UpdateProgress (Result Http.Error Progress)
    | EncodedAuth String


type Status
    = Unknown
    | Created
    | Exists
    | Error


type alias Progress =
    { database : Status
    , ssh_user : Status
    , configuration : Status
    , ssh_commands : Status
    , url : String
    , logs : Maybe String
    }


type alias Model =
    { email : String
    , password : String
    , deploySuccess : Maybe String
    , error : Maybe Http.Error
    , progress : Progress
    , encodedAuth : String
    }


init : ( Model, Cmd Msg )
init =
    Model "" "" Nothing Nothing (Progress Unknown Unknown Unknown Unknown "" Nothing) "" ! []



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
                | error = Just error
                , deploySuccess = Nothing
            }
                ! []

        CheckProgress _ ->
            model ! [ checkProgress model.encodedAuth ]

        UpdateProgress (Ok progress) ->
            { model | progress = progress } ! []

        UpdateProgress (Err error) ->
            { model | error = Just error } ! []

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


stringToStatus : String -> Status
stringToStatus status =
    case status of
        "unknown" ->
            Unknown

        "created" ->
            Created

        "exists" ->
            Exists

        _ ->
            Error


statusDecoder : Decode.Decoder Status
statusDecoder =
    Decode.map stringToStatus Decode.string


progressDecoder : Decode.Decoder Progress
progressDecoder =
    Decode.map6 Progress
        (Decode.at [ "status", "database" ] statusDecoder)
        (Decode.at [ "status", "ssh_user" ] statusDecoder)
        (Decode.at [ "status", "configuration" ] statusDecoder)
        (Decode.at [ "status", "ssh_commands" ] statusDecoder)
        (Decode.field "url" Decode.string)
        (Decode.field "logs" (Decode.nullable Decode.string))


checkProgress : String -> Cmd Msg
checkProgress basicAuth =
    Http.send UpdateProgress <|
        Http.request
            { method = "GET"
            , headers = [ Http.header "Authorization" ("Basic " ++ basicAuth) ]
            , url = statusUrl
            , body = Http.emptyBody
            , expect = Http.expectJson progressDecoder
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
    in
        Html.div
            []
            [ body ]


viewError : Maybe Http.Error -> Html.Html Msg
viewError error =
    case error of
        Just err ->
            let
                ( title, error ) =
                    case err of
                        Http.BadStatus _ ->
                            ( "The form contains errors"
                            , "Your credentials are incorrect"
                            )

                        _ ->
                            ( "Server error", "Server unreachable" )
            in
                Html.div
                    [ Html.Attributes.class "errors" ]
                    [ Html.h3 [] [ Html.text title ]
                    , Html.ul
                        []
                        [ Html.li [] [ Html.text error ] ]
                    ]

        Nothing ->
            Html.div [] []


viewForm : Model -> Html.Html Msg
viewForm model =
    Html.form
        [ Html.Attributes.class "login-holder"
        , Html.Attributes.action "#"
        ]
        [ Html.h1 [] [ Html.text "Login and deploy Kinto" ]
        , Html.div
            [ Html.Attributes.class "well"
            , Html.Attributes.style [ ( "background-color", "#efefef" ) ]
            ]
            [ Html.text "This will install kinto in the "
            , Html.code [] [ Html.text "/www/" ]
            , Html.text "directory of your account to make it run behind HTTPS on "
            , Html.code [] [ Html.text "<username>.alwaysdata.net" ]
            , Html.br [] []
            , Html.b [] [ Html.text "Make sure to save its content first." ]
            , Html.br [] []
            , Html.text "It will create a PostgreSQL database and a SSH user."
            ]
        , Html.div
            [ Html.Attributes.class "well"
            , Html.Attributes.style [ ( "background-color", "#efefef" ) ]
            ]
            [ viewError model.error
            , Html.div
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


statusToGlyph : String -> Status -> Html.Html Msg
statusToGlyph title status =
    let
        glyph =
            case status of
                Unknown ->
                    "fa-spinner fa-pulse"

                Created ->
                    "fa-thumbs-up"

                Exists ->
                    "fa-thumbs-up"

                Error ->
                    "fa-thumbs-down"
    in
        Html.li []
            [ Html.text title
            , Html.i
                [ Html.Attributes.class <| "fa fa-fw " ++ glyph
                , Html.Attributes.style [ ( "float", "right" ) ]
                ]
                []
            ]


viewProgress : Model -> Html.Html Msg
viewProgress model =
    let
        progress =
            model.progress

        deployDone =
            progress.ssh_commands == Created

        title =
            if deployDone then
                "Kinto has been deployed!"
            else
                "Deploying Kinto, please wait"

        links =
            if deployDone then
                Html.div
                    []
                    [ Html.a
                        [ Html.Attributes.href
                            "https://admin.alwaysdata.com/site/"
                        ]
                        [ Html.text "Manage your kinto!" ]
                    , Html.a
                        [ Html.Attributes.href progress.url
                        , Html.Attributes.style [ ( "float", "right" ) ]
                        ]
                        [ Html.text "Access your kinto!" ]
                    ]
            else
                Html.text ""

        body =
            Html.div []
                [ Html.ul []
                    [ statusToGlyph "Database: " progress.database
                    , statusToGlyph "SSH user: " progress.ssh_user
                    , statusToGlyph "Configuration: " progress.configuration
                    , statusToGlyph "SSH commands: " progress.ssh_commands
                    ]
                ]
    in
        Html.div
            [ Html.Attributes.class "login-holder" ]
            [ Html.h1 [] [ Html.text title ]
            , Html.div
                [ Html.Attributes.class "well"
                , Html.Attributes.style [ ( "background-color", "#efefef" ) ]
                ]
                [ body
                , links
                ]
            , Html.pre
                [ Html.Attributes.style [ ( "max-height", "200px" ) ] ]
                [ Html.text <| Maybe.withDefault "" progress.logs ]
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
