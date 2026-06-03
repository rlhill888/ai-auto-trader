"use client";

import { useEffect } from "react";
import * as Ably from "ably";

let client: Ably.Realtime | null = null;

function getClient(): Ably.Realtime {
  if (!client) {
    client = new Ably.Realtime({ authUrl: "/api/ably/token" });
  }
  return client;
}

export function useAblyChannel(
  channelName: string,
  eventName: string,
  onMessage: (msg: Ably.Message) => void
) {
  useEffect(() => {
    const channel = getClient().channels.get(channelName);
    channel.subscribe(eventName, onMessage);
    return () => {
      channel.unsubscribe(eventName, onMessage);
    };
  }, [channelName, eventName, onMessage]);
}
