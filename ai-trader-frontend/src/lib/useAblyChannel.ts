"use client";

import { useEffect } from "react";
import * as Ably from "ably";

let client: Ably.Realtime | null = null;

function getClient(): Ably.Realtime {
  if (!client) {
    console.log("[Ably] Creating new Realtime client");
    client = new Ably.Realtime({ authUrl: "/api/ably/token" });

    client.connection.on((stateChange) => {
      console.log(`[Ably] Connection state: ${stateChange.current}`, stateChange.reason ?? "");
    });
  }
  return client;
}

export function useAblyChannel(
  channelName: string,
  eventName: string,
  onMessage: (msg: Ably.Message) => void
) {
  useEffect(() => {
    console.log(`[Ably] Subscribing to channel="${channelName}" event="${eventName}"`);
    const channel = getClient().channels.get(channelName);
    channel.subscribe(eventName, (msg) => {
      console.log(`[Ably] Message received on channel="${channelName}" event="${eventName}"`, msg.data);
      onMessage(msg);
    });
    return () => {
      console.log(`[Ably] Unsubscribing from channel="${channelName}" event="${eventName}"`);
      channel.unsubscribe(eventName, onMessage);
    };
  }, [channelName, eventName, onMessage]);
}
