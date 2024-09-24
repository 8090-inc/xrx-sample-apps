class AudioProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    const channel = input[0];

    if (channel && channel.length > 0) {
      const pcmData = new Int16Array(channel.length);

      for (let i = 0; i < channel.length; i++) {
        const normalizedSample = Math.max(-1, Math.min(1, channel[i]));
        pcmData[i] =
          normalizedSample < 0
            ? normalizedSample * 0x8000
            : normalizedSample * 0x7fff;
      }

      this.port.postMessage({ pcmData });
    }

    return true;
  }
}

registerProcessor("audio-processor", AudioProcessor);
