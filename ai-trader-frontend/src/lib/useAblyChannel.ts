"use client";

import { useEffect, useRef } from "react";
import * as Ably from "ably";

let client: Ably.Realtime | null = null;

function getClient(): Ably.Realtime {
  if (!client) {
    client = new Ably.Realtime({
      authUrl: "/api/ably/token",
      autoConnect: true
    });
  }
  return client;
}

export function useAblyChannel(
  channelName: string,
  eventName: string,
  onMessage: (msg: Ably.Message) => void
) {
  const onMessageRef = useRef(onMessage);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    const channel = getClient().channels.get(channelName);

    const failedHandler = (stateChange: Ably.ChannelStateChange) => {
      console.error(`[Ably] Channel "${channelName}" failed:`, stateChange.reason);
    };

    channel.on('failed', failedHandler);

    const listener = (msg: Ably.Message) => {
      onMessageRef.current(msg);
    };

    channel.subscribe(eventName, listener);

    return () => {
      channel.unsubscribe(eventName, listener);
      channel.off('failed', failedHandler);
    };
  }, [channelName, eventName]);
}
