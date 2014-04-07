var CONFIG = require('config').AMQP;
var rabbit = require('rabbit.js');
var context;

function emit(target, message) {
    console.log("Emitting " + message + " to " + target + "...");
    var push = context.socket('PUSH');
    push.connect(target, function() {
        push.write(JSON.stringify({id:Date.now(), message:message}), 'utf8');
        push.end();
    });
}

function messager() {
    if (process.argv.length !== 4)
    {
        console.log("Usage: node messager.js target-user message");
        return;
    }
    var target = process.argv[2];
    var message = process.argv[3];
    context = rabbit.createContext(CONFIG.Url);
    context.on("ready", function() {
        emit(target, message);
    });
}

messager();
