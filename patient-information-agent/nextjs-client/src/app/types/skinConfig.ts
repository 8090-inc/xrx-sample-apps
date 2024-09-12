interface SkinConfig {
  buttonText: string;
  logoSrc: string;
  welcomeText?: string;
  welcomeScreenLogoSrc: string;
  greetingSrc: string;
  styles: {
    backgroundColor: string;
    secondaryColor: string;
    mainFont: string;
    logoBackgroundColor: string;
    fontColorOnBackground: string;
    speakingPulseColor: string;
    thinkingColor: string;
  };
}

const SkinConfigurations: Record<string, SkinConfig> = {
  "patient-information-agent": {
    buttonText: "Start",
    welcomeText: "Patient Intake",
    logoSrc: "/hospital-logo.png",
    welcomeScreenLogoSrc: "/hospital-logo.png",
    greetingSrc: "/patient-info-start.mp3",
    styles: {
      backgroundColor: "#f9f7f4",
      secondaryColor: "#54c1c2",
      mainFont: "Open Sans, Arial, Helvetica, sans-serif",
      logoBackgroundColor: "white",
      fontColorOnBackground: "#333",
      speakingPulseColor: "#54c1c2",
      thinkingColor: "#54c1c2"
    }
  }
};

export type { SkinConfig };
export { SkinConfigurations };
