import type { Metadata } from "next";
import DienstPageLayout from "@/components/diensten/DienstPage";

export const metadata: Metadata = {
  title: "Rookdetectie in Antwerpen-Stad | Turbo Services",
  description: "Betrouwbare rookdetectie oplossingen voor woningen en bedrijven in Antwerpen-Stad. Bescherm uw eigendom met Turbo Services.",
};

export default function Page() {
  return (
    <DienstPageLayout
      brand="Turbo Services"
      regionLabel="Antwerpen-Stad"
      serviceName="Rookdetectie"
      h1="Veiligheid voorop met rookdetectie in Antwerpen-Stad"
      intro="Turbo Services biedt professionele rookdetectie systemen aan in Antwerpen-Stad. Onze oplossingen zorgen voor een snelle detectie van rook en brand, zodat u en uw eigendom optimaal beschermd zijn."
      heroImageKey="/assets/generated/rookdetectie-antwerpen-stad.webp"
      sections=[{"title": "Waarom rookdetectie essentieel is", "body": "Rookdetectie is cruciaal om vroegtijdig brand te signaleren en zo levens en eigendommen te beschermen. In dichtbevolkte gebieden zoals Antwerpen-Stad is een betrouwbare rookmelder onmisbaar voor zowel woningen als bedrijven."}, {"title": "Onze diensten en expertise", "body": "Bij Turbo Services installeren en onderhouden we rookdetectiesystemen die voldoen aan de hoogste veiligheidsnormen. Onze experts adviseren u over de beste oplossingen op maat van uw situatie in Antwerpen-Stad."}]
      cta={"title": "Bescherm uw woning of bedrijf vandaag nog", "button": "Contacteer ons nu", "phone": "0479 20 40 69"}
    />
  );
}
