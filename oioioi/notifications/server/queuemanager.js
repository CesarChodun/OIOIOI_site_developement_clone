var rabbit = require('rabbit.js');
var EventEmitter = require('events').EventEmitter;
var eventEmitter = new EventEmitter();
var CONFIG = require('config').AMQP;
var context;
var workers = {};
var unackMessages = {};

function init(_context, onCompleted) {
    context = _context;
    if (!context) {
        context = rabbit.createContext(CONFIG.Url);
    }
    context.on('ready', function() {
        onCompleted();
    });
    context.on('error', function(e) {
        console.log('RabbitMQ error!');
        console.log(e.toString());
    });
}

function subscribe(userName) {
    if (workers[userName]) {
        return;
    }
    workers[userName] = context.socket('WORKER');
    workers[userName].connect(userName);
    unackMessages[userName] = {};

    workers[userName].on('data', function(data) {
       try {
           data = JSON.parse(data);
       } catch(obj) {
           // remove bad message from queue
           console.log('Bad message format arrived!');
           workers[userName].ack();
       }
       unackMessages[userName][data.id] = data;
       eventEmitter.emit('message', userName, data);
    });
}

function unsubscribe(userName) {
    if (!workers[userName]) {
        return;
    }
    workers[userName].close();
    delete workers[userName];
}

function unsubscribeAll() {
    for (var userName in workers) {
        unsubscribe(userName);
    }
}

function acknowledge(userName, messageId) {
    if (unackMessages[userName] &&
        Number(Object.keys(unackMessages[userName])[0]) === messageId) {
        workers[userName].ack();
        delete unackMessages[userName][messageId];
        console.log('Acknowledged msgid '+ messageId);
        return true;
    }
    return false;
}

function getUnacknowledgedMessages(userName) {
    return unackMessages[userName];
}

exports.init = init;
exports.getUnacknowledgedMessages = getUnacknowledgedMessages;
exports.subscribe = subscribe;
exports.unsubscribe = unsubscribe;
exports.acknowledge = acknowledge;
exports.unsubscribeAll = unsubscribeAll;
exports.on = eventEmitter.on.bind(eventEmitter);
