"use client";

import { useEffect, useRef } from "react";
import * as Ably from "ably";

let client: Ably.Realtime | null = null;

function getClient(): Ably.Realtime {
  if (!client) {
    console.log("[Ably] Creating new Realtime client");
    client = new Ably.Realtime({ authUrl: "/api/ably/token" });

    client.connection.on((stateChange) => {
      console.log(`[Ably] Connection state: ${stateChange.current}`, stateChange.reason ?? "");
    });

    client.connection.on("connected", () => {
      console.log("[Ably] Connected. Connection ID:", client!.connection.id);
      client!.channels.get("trading").subscribe((msg) => {
        console.log("[Ably ROOT]", msg.name, msg.data);
      });
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

    // Monitor channel state for debugging
    const attachedHandler = (stateChange: Ably.ChannelStateChange) => {
      console.log(`[Ably] Channel "${channelName}" attached. Resumed: ${stateChange.resumed}`);
    };

    const failedHandler = (stateChange: Ably.ChannelStateChange) => {
      console.error(`[Ably] Channel "${channelName}" failed:`, stateChange.reason);
    };

    channel.on('attached', attachedHandler);
    channel.on('failed', failedHandler);

    const listener = (msg: Ably.Message) => {
      console.log(`[Ably] Message received on channel="${channelName}" event="${eventName}"`, msg.data);
      onMessageRef.current(msg);
    };

    console.log(`[Ably] Subscribing to channel="${channelName}" event="${eventName}"`);
    channel.subscribe(eventName, listener);

    return () => {
      console.log(`[Ably] Unsubscribing from channel="${channelName}" event="${eventName}"`);
      channel.unsubscribe(eventName, listener);
      channel.off('attached', attachedHandler);
      channel.off('failed', failedHandler);
    };
  }, [channelName, eventName]);
}
