const PollSocket = (() => {
  let socket = null;

  function connect() {
    if (socket) {
      return socket;
    }

    socket = io();

    socket.on("connect", () => {
      console.log("Socket connected:", socket.id);
    });

    socket.on("disconnect", () => {
      console.log("Socket disconnected.");
    });

    socket.on("connection_status", (data) => {
      console.log("Connection status:", data);
    });

    socket.on("socket_error", (data) => {
      console.error("Socket error:", data);
    });

    return socket;
  }

  function joinPoll(pollCode) {
    if (!socket) {
      connect();
    }

    socket.emit("join_poll", {
      poll_code: pollCode,
    });
  }

  function leavePoll(pollCode) {
    if (!socket) {
      return;
    }

    socket.emit("leave_poll", {
      poll_code: pollCode,
    });
  }

  function on(eventName, callback) {
    if (!socket) {
      connect();
    }

    socket.on(eventName, callback);
  }

  function emit(eventName, data) {
    if (!socket) {
      connect();
    }

    socket.emit(eventName, data);
  }

  return {
    connect,
    joinPoll,
    leavePoll,
    on,
    emit,
  };
})();
