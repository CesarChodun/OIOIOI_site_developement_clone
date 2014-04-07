How to prepare:
- install and run rabbitmq-server
- ensure it works on localhost on default port or enjoy tinkering with settings (config/default.yaml)

How to run this server:
- in this directory, invoke: npm install
- then, invoke: npm start

How to run tests:
- sudo npm install --global mocha
- in this directory, invoke: npm test

How to test this in action:
- type: node messager.js target-user-name message
and watch the message arrive to target user

This whole solution is in total alpha stage and it will probably change a lot,
however it's fully functional right now and supports multiple logged in clients
under the same username as well as message acknowledgement.
