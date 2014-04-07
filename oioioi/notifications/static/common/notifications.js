var NUMBER_BADGE = "#notifications_number";
var TABLE_NOTIFICATIONS = "#balloon_table_notifications";
var NO_NOTIFICATIONS = "#info_no_notifications";
var socket;
var inited = false;
var notifCount = 0;
var unconfirmedMessages = [];
var messages = {};

function init() {
    if (inited) {
        return;
    }
    inited = true;
    if (typeof(io) === 'undefined')
    {
        setErrorState();
        return;
    }
    renderMessages();
    $(NUMBER_BADGE).on("click", acknowledgeMessages);
    socket = io.connect(NOTIF_SERVER_URL);
    socket.on('connect', authenticate);
    socket.emits = function(k, v) {
        socket.emit(k, JSON.stringify(v));
    };
    setInterval(notifWatchdog, 2000);
    socket.on("message", onMessageReceived);
    socket.on("ack_nots", onAcknowledgeCompleted);
}

function getCookieByName(name) {
    var cookieMap = document.cookie.split('; ').map(function(t) { return t.split('='); });
    for (var cookieId in cookieMap) {
        if (cookieMap[cookieId][0] === name) {
            return cookieMap[cookieId][1];
        }
    }
    return undefined;
}

function notifWatchdog() {
    if (!socket || !socket.socket.connected) {
        setErrorState();
    }
}

function setErrorState() {
    $(NUMBER_BADGE).text('!');
    $(NUMBER_BADGE).removeClass("label-primary");
    $(NUMBER_BADGE).removeClass("label-success");
    $(NUMBER_BADGE).addClass("label-warning");
}

function authenticate() {
    var sid = getCookieByName('sessionid');
    socket.emits("authenticate", {session_id: sid});
    socket.on("authenticate", function(result)
    {
        if (result.status !== 'OK') {
            setErrorState();
        }
        else {
            notifCount = 0;
            updateNotifCount();
        }
    });
}

function updateNotifCount() {
    $(NUMBER_BADGE).text(notifCount);
    $(NUMBER_BADGE).removeClass("label-primary");
    $(NUMBER_BADGE).removeClass("label-success");
    $(NUMBER_BADGE).removeClass("label-warning");
    $(NUMBER_BADGE).addClass(notifCount > 0 ? "label-success" : "label-primary");
}

function renderMessages() {
    var content = '<colgroup><col width="50px"/><col/></colgroup>';
    var wereMessages;
    var msgKeys = Object.keys(messages)
        .sort(function(a,b) { return Number(a) < Number(b); });

    for (var msgKeyId in msgKeys) {
        wereMessages = true;
        content += '<tr><td></td><td>' + messages[msgKeys[msgKeyId]].message +
            '</td></tr>';
    }

    $(NO_NOTIFICATIONS).toggle(!wereMessages);
    $(TABLE_NOTIFICATIONS).html(content);
}

function onMessageReceived(message) {
    if (messages[message.id]) {
        return;
    }
    messages[message.id] = message;
    renderMessages();

    ++notifCount;
    updateNotifCount();
    unconfirmedMessages.push(message.id);
}

function onAcknowledgeCompleted(result) {
    if (result && result.status === 'OK') {
        notifCount = 0;
        updateNotifCount();
    }
}

function acknowledgeMessages() {
    if (unconfirmedMessages.length > 0) {
        socket.emits("ack_nots", unconfirmedMessages);
    }
}

$(document).ready(init);