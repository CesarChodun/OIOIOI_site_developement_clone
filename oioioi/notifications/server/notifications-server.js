var http = require('http'),
    io = require('socket.io'),
    rabbit = require('rabbit.js'),
    auth = require('./auth'),
    queuemanager = require('./queuemanager'),
    CONFIG = require('config');

var last_dict_id = 0;
var app;

function handler(_, res) {
    res.writeHead(200);
    res.end('Welcome to OIOIOI Notifications Server. ' +
        'This server is available for purpose of serving online notifications. ' +
        'This server does not host a functional website itself.');
}

function onSocketConnected(socket) {
    configureSocket(socket);
}

function configureSocket(socket) {
    socket.dict_id = last_dict_id++;
    console.log("Connected socket " + socket.dict_id);
    socket.on('authenticate', respond('authenticate', socket, onAuthenticateRequested));
    socket.on('ack_nots', respond('ack_nots', socket, onAckNotsRequested));
}

function runServer() {
    queuemanager.init(rabbit.createContext(CONFIG.AMQP.Url), function() {
        app = http.createServer(handler);
        queuemanager.on('message', onMessageReceived);
        io.listen(app).sockets.on('connection', onSocketConnected);
        app.listen(CONFIG.Server.Port);
        console.log('Notifications Server listening on port ' + CONFIG.Server.Port);
    });
}

function respond(key, socket, handler) {
    return function(data) {
        var userName = auth.resolveUserName(socket);
        handler(JSON.parse(data), userName, socket, function(response) {
            socket.emit(key, response);
        });
    };
}

function onMessageReceived(userName, message) {
    console.log('User ' + userName + ' sent message: ' + JSON.stringify(message));
    var clients = auth.getClientsForUser(userName);
    for (var clientId in clients) {
        clients[clientId].emit("message", message);
    }
}

function onAuthenticateRequested(data, _, socket, onCompleted) {
    if (!data || !data.session_id) {
        return {status: 'ERR_INVALID_MESSAGE'};
    }
    auth.login(socket, data.session_id, function(userName) {
        onCompleted(userName ? {status: 'OK'} : {status: 'ERR_AUTH_FAILED'});
        // when a new user logs in, let him know what's up!
        retransmitNotifications(userName);
    });
}

function retransmitNotifications(userName) {
    var messages = queuemanager.getUnacknowledgedMessages(userName);
    for (var msgId in messages) {
        onMessageReceived(userName, messages[msgId]);
    }
}

function onAckNotsRequested(nots, userName, _, onCompleted) {
    if (!userName) {
        onCompleted({status: 'ERR_UNAUTHORIZED'});
        return;
    }

    for (var notId in nots) {
        queuemanager.acknowledge(userName, nots[notId]);
    }

    onCompleted({status: 'OK'});
}

exports.onSocketConnected = onSocketConnected;
exports.onMessageReceived = onMessageReceived;
exports.runServer = runServer;