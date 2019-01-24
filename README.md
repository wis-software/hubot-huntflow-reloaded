# hubot-huntflow-reloaded

hubot-huntflow-reloaded is a project intended to move the [Huntflow](https://huntflow.ru) reminders to a team chat (based on [Rocket.Chat](https://rocket.chat/)).

The project is split into two parts: server and client. The server side is a Huntflow webhook handler. When Huntflow sends a POST request to the server, the server, in turn, pulls the events from the requests, schedules and sends them to the client, a Hubot script, via a Redis broker (the client subscribes to the channel and the server publishes the message to the channel). 

## Table of Contents

- [Client](#client)
- [Server](#server)
- [Authors](#authors)
- [Licensing](#licensing)

## Client

The client is a Hubot script intended to receive the reminders from the Redis channel and pass them to the specified Rocket.Chat channel. 

### Installation

In hubot project repo, run:

`npm install git+https://github.com/tolstoyevsky/hubot-huntflow-reloaded --save`

Then add **hubot-huntflow-reloaded** to your `external-scripts.json`:

```json
[
  "hubot-huntflow-reloaded"
]
```

## Server

TODO: describe the server

### Installation

TODO: describe how to install the server

## Authors

See [AUTHORS](AUTHORS.md).

## Licensing

hubot-huntflow-reloaded is available under the [Apache License, Version 2.0](LICENSE).
