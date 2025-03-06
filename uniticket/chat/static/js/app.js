var currentRecipient = '';
var currentRecipient_fullname = '';
var chatInput = $('#chat-input');
var chatButton = $('#btn-send');
var videoChatButton = $('#btn-videochat');
var userList = $('#user-list');
var messageList = $('#messages');
var users = [];

// timeout
var timeout_milliseconds = 40000;
var timeout = null;

// play sound
function beep(){
    document.getElementById("beep_sound").play();
}

// generate uuid4 code
function uuid4(){
    var uuid = '', ii;
    for (ii = 0; ii < 32; ii += 1) {
        switch (ii) {
            case 8:
            case 20:
                uuid += '-';
                uuid += (Math.random() * 16 | 0).toString(16);
                break;
            case 12:
                uuid += '-';
                uuid += '4';
                break;
            case 16:
                uuid += '-';
                uuid += (Math.random() * 4 | 8).toString(16);
                break;
            default:
                uuid += (Math.random() * 16 | 0).toString(16);
        }
    }
    return uuid;
}

// return true if user is in current users[] list
function user_is_in_list(user) {
    return users.indexOf(parseInt(user))>=0;
}

// return true if current user is in chat with a user
function active_chat_with(user){
    return user_is_in_list(user) && user==currentRecipient;
}

// return true if current user is in chat with a user not in list
function inactive_chat_with(user){
    if(user==currentUser)return false;
    return user==currentRecipient &! user_is_in_list(user);
}

// make css inactive all users
function make_inactive_all() {
    $( "a.user" ).removeClass("active");
}

// make css active a user
function make_active(user) {
    $( "a.user[user='" + user + "']" ).addClass("active");
    $( "a.user[user='" + user + "']" ).removeClass("text-secondary");
}

// make css unread a user
function make_unread(user) {
    $( "a.user[user='" + user + "']" ).addClass("text-secondary");
    beep();
}

// return true if a message is for active chat
function message_is_for_active_chat(sender, recipient) {
    if(sender == currentRecipient) return true;
    if(recipient == currentRecipient && sender == currentUser) return true;
    return false;
}

// operator changed status
function operatorStatusChanged(user, status) {
    if (user != currentUser)
        if (status)
            $( "#" + user + "_status" ).replaceWith(`<svg class="me-2 icon icon-success icon-xs" id="`+ user + `_status">
                                                        <use xlink:href="/static/svg/sprites.svg#it-check-circle"></use>
                                                        <title>Disponibile</title>
                                                    </svg>`);
        else
            $( "#" + user + "_status" ).replaceWith(`<svg class="me-2 icon icon-danger icon-xs" id="`+ user + `_status">
                                                          <use xlink:href="/static/svg/sprites.svg#it-minus-circle"></use>
                                                          <title>Occupato</title>
                                                       </svg>`);
}

// add onClick event to user button
function addClickEvent(){
    // add click event
    $(userList).children('.item').last().children('.user').first().on("click",
        function () {
            var target = $(event.target);
            userList.children('.item').children('.active').removeClass('active');
            target.addClass('active');
            setCurrentRecipient(username=target.attr('user'),
                                full_name=target.text(),
                                room_name=room_name);
        }
    );
}

// add remove onClick event to user cross button
function addRemoveEvent(){
    // add delete click event
    $(userList).children('.item').last().children('.item_delete').first().on("click",
        function () {
            var user_to_remove = $(event.target).parent().children('.user').first().attr('user');
            removeUserFromList(user=user_to_remove,
                               manual_remove=true);
        }
    );
}

// add a user div in list
function addUserDiv(user, user_fullname, is_operator, operator_status=true) {

    // if current user is already logged in chat
    // (for example in another browser tab)
    // than don't show (duplicate) button
    if (!($("[user="+user+"]").length)){
        // build HTML user element in list
        var userItem = `<div class="item mb-2">
                            <a role="button" user="${user}" class="user btn btn-outline-secondary w-75 p-3">`;
        if (is_operator && user != currentUser){
            if (operator_status)
                userItem += `<svg class="me-2 icon icon-success icon-xs" id="`+ user + `_status">
                                <use xlink:href="/static/svg/sprites.svg#it-check-circle"></use>
                                <title>Disponibile</title>
                            </svg>`;
            else
                userItem += `<svg class="me-2 icon icon-danger icon-xs" id="`+ user + `_status">
                                <use xlink:href="/static/svg/sprites.svg#it-minus-circle"></use>
                                <title>Occupato</title>
                            </svg>`;
        }
        if (user == currentUser) userItem += `Scrivi a tutti</a>`;
        else userItem += `${user_fullname}</a>`;

        if (currentUser != user)
            userItem += `<svg class="icon icon-secondary icon-xs ml-2 item_delete">
                            <use xlink:href="/static/svg/sprites.svg#it-close-circle"></use>
                            <title>Rimuovi dalla lista</title>
                        </svg>`;
        userItem += `</div>`;

        $(userItem).appendTo(userList);
        addClickEvent();
        addRemoveEvent();
    }
}

// draw a message in chat
function drawMessage(message, user_fullname, from_bot=false) {
    console.log("drawMessage " + message);
    var avatar = currentRecipient_fullname;
    if (user_fullname) avatar = user_fullname;
    if (message.user == currentUser) avatar = 'io';
    var position = 'left';
    if (from_bot) {
        var date = new Date();
        var msg_body = message;
    } else {
        var date = new Date(message.created);
        if (message.user == currentUser) position = 'right';
        var msg_body = message.body;
    }
    const messageItem = `
            <li class="message ${position}">
                <div class="avatar">
                    <span>${avatar}</span>
                </div>
                <div class="text_wrapper">
                    <div class="text">${msg_body}<br>
                        <span class="text-muted chat-date-info">${date}</span>
                    </div>
                </div>
            </li>`;
    $(messageItem).appendTo('#messages');
}

// show messages of a conversation
function getConversation(recipient, room_name) {
    console.log("getConversation " + recipient);
    $.getJSON(`/api/chat/message/?target=${recipient}&room=${room_name}`, function (data) {
        messageList.children().remove();
        for (var i = data['results'].length - 1; i >= 0; i--) {
            console.log("getConversation " + data['results'][i]);
            drawMessage(message=data['results'][i]);
        }
        make_inactive_all();
        make_active(currentRecipient);
        messageList.animate({scrollTop: messageList.prop('scrollHeight')});
    });
}

// add user in users list
function addUserInList(user,
                       user_fullname,
                       is_operator=false,
                       operator_status=true,
                       block_bot=false) {
    console.log("currentrecipient: "+ currentRecipient);
    if (!user_is_in_list(user)) {
        addUserDiv(user=user,
                   user_fullname=user_fullname,
                   is_operator=is_operator,
                   operator_status=operator_status);
        if (user != currentUser) users.push(parseInt(user));
        if (user == currentRecipient) {
            //if(!block_bot)
                //drawMessage(message="L'utente è rientrato nella chat",
                            //user_fullname='BOT',
                            //from_bot=true);
            //messageList.animate({scrollTop: messageList.prop('scrollHeight')});
            enableInput();
            make_active(user);
        } else if (currentRecipient && block_bot) {
            make_active(user);
            //make_unread(user);
        }
    //} else if (user != currentRecipient) {
        //make_unread(user);
    }
}

// remove a user from list
function removeUserFromList(user, manual_remove=false) {
    console.log("removeUserFromList:" + user);
    $("a.user[user='"+ user +"']").parent().remove();
    console.log(users);
    var user_index = users.indexOf(parseInt(user))
    users.splice(user_index, 1);
    console.log("Users list after remove: " + user);
    // if currentRecipient leaves the room, you can't write anymore
    if (user == currentRecipient){
        //if (!manual_remove) {
            //drawMessage(message="L'utente ha abbandonato la chat",
                        //user_fullname='BOT',
                        //from_bot=true);
            //messageList.animate({scrollTop: messageList.prop('scrollHeight')});
        //}
        disableInput();
    }
    //currentRecipient = null;
    console.log(users);
}

// get a message from API
function getMessageById(message, room_name, is_operator=false, operator_status=true) {
    id = JSON.parse(message).message;
    user_fullname = JSON.parse(message).user_fullname;
    console.log("getMessageById: " + currentRecipient);

    $.getJSON(`/api/chat/message/${id}/?room=${room_name}`, function (data) {
        if(message_is_for_active_chat(sender=data.user,
                                      recipient=data.recipient)){
            if(inactive_chat_with(data.user)){
                addUserInList(user=data.user,
                              user_fullname=user_fullname,
                              is_operator=is_operator,
                              operator_status=operator_status,
                              block_bot=true);
                make_active(data.user);
                beep();
            }
            enableInput();
            drawMessage(message=data,
                        user_fullname=user_fullname);
            messageList.animate({scrollTop: messageList.prop('scrollHeight')});
        }
        else {
            if(!user_is_in_list(data.user)) {
                addUserInList(user=data.user,
                              user_fullname=user_fullname,
                              is_operator=is_operator,
                              operator_status=operator_status,
                              block_bot=true);
            }
            make_unread(data.user);
        }
    });
}

// update user channel status via API post
function updateUserStatus() {
    $.ajax({
        url: '/api/chat/user/' + currentUser +'/',
        type: 'PUT',
        data: {
            room: room_name,
        },
        fail: function () {
            alert('Error! Check console!');
        }
    });
}

// create a message via API post
function sendMessage(recipient, room_name, body, broadcast=0) {
    console.log("sendMessage / broadcast " + broadcast);
    $.post('/api/chat/message/', {
        recipient: recipient,
        room: room_name,
        body: body,
        broadcast: broadcast
    }).fail(function () {
        alert('Error! Check console!');
    });
}

// set a user as currentRecipient
function setCurrentRecipient(username, full_name, room_name) {
    currentRecipient = username;
    currentRecipient_fullname = full_name;
    getConversation(recipient=currentRecipient, room_name=room_name);
    enableInput();
}

// enable input field
function enableInput() {
    chatInput.prop('disabled', false);
    chatButton.prop('disabled', false);
    if (currentRecipient!=currentUser) videoChatButton.prop('disabled', false);
    chatInput.focus();
}

// disable input field
function disableInput() {
    chatInput.prop('disabled', true);
    chatButton.prop('disabled', true);
    videoChatButton.prop('disabled', true);
}

function reloadPage() {
    window.location.hash = '#leave_chat_button';
    window.location.reload(true);
}

function reset_timeout() {
    // clear timeout and redefine a new
    clearTimeout(timeout);
    timeout = setTimeout(reloadPage, timeout_milliseconds);
}

$(document).ready(function () {
    // disable input field
    disableInput();

    // set socket
    var socket = new WebSocket(
        ws_protocol + window.location.host +
        '/ws/chat/' + room_name + '/?session_key=' + sessionKey);
    console.log(socket);

    // set timeout to reloadPage
    timeout = setTimeout(reloadPage, timeout_milliseconds);

    // on ENTER click
    chatInput.keypress(function (e) {
        if (e.keyCode == 13)
            chatButton.click();
    });

    // onclick to send button
    chatButton.click(function () {
        if (chatInput.val().length > 0) {
            // broadcast message to all users of room
            if (currentRecipient==currentUser) {
                for (var i=0; i<users.length; i++) {
                    sendMessage(recipient=users[i],
                                room_name=room_name,
                                body=chatInput.val(),
                                broadcast=1);
                }
            } else {
                sendMessage(recipient=currentRecipient,
                            room_name=room_name,
                            body=chatInput.val());
            }
            chatInput.val('');
        }
    });

    // onclick to videochat button
    videoChatButton.click(function () {
        videochat_text="Clicca qui per entrare in videoconferenza ";
        xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", '/chat/random-vc-provider', false );
        xmlHttp.send();
        videochat_url = xmlHttp.responseText + uuid4();
        window.open(videochat_url, '_blank');
        sendMessage(recipient=currentRecipient,
                    room_name=room_name,
                    body=videochat_text + " " + videochat_url);
    });

    // on socket message
    socket.onmessage = function (e) {
        json_data = JSON.parse(e.data);
        console.log("socket.onmessage: " + json_data);

        // clear timeout and redefine a new
        reset_timeout();
        //clearTimeout(timeout);
        //timeout = setTimeout(reloadPage, timeout_milliseconds);

        if (json_data['command'])
            switch (json_data['command']) {
                case 'join_room':
                    console.log("received join room: " + json_data['user']);
                    console.log(json_data);
                    addUserInList(user=json_data['user'],
                                  user_fullname=json_data['user_fullname'],
                                  is_operator=json_data['is_operator'],
                                  operator_status=json_data['operator_status']);
                    break;
                case 'leave_room':
                    console.log("received leave room: " + json_data['user']);
                    removeUserFromList(user=json_data['user']);
                    break;
                case 'add_user':
                    console.log("add user: " + json_data['user']);
                    console.log(json_data);
                    console.log(json_data['operator_status']);
                    addUserInList(user=json_data['user'],
                                  user_fullname=json_data['user_fullname'],
                                  is_operator=json_data['is_operator'],
                                  operator_status=json_data['operator_status']);

                    break;
                case 'update_operator_status':
                    console.log("user: " + json_data['user'] + " changed his status " + json_data['status']);
                    operatorStatusChanged(user=json_data['user'],
                                          status=json_data['status']);
                    break;
            }
        else if (json_data['message']) {
            console.log("message: " + e.data);
            getMessageById(message=e.data,
                           room_name=room_name,
                           is_operator=json_data['is_operator'],
                           operator_status=json_data['operator_status']);
        }
    };
});
