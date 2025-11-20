import type { Metadata } from "next";
import { DienstPageLayout, type DienstPageProps } from "@/components/diensten/DienstPage";

export const metadata: Metadata = {
  title: "Ontstoppingen in Antwerpen Stad | Turbo Services",
  description: "Ontstopping van wc, lavabo, douche en hoofdriolering. Turbo Services lost verstoppingen snel en professioneel op, ook ’s avonds en in het weekend aan hetzelfde tarief.",
};

const pageProps: DienstPageProps = {
  brand: "Turbo Services",
  serviceName: "Ontstoppingen",
  regionLabel: "Antwerpen Stad",
  heroTitle: "Ontstoppingen",
  intro: "Verstopte wc, lavabo, douche of hoofdriolering in Antwerpen Stad? Turbo Services lost het op met professionele machines, ook ’s avonds en in het weekend aan hetzelfde tarief.",
  sections: [
    {
      title: "Wat we doen",
      bullets: ["Verstopte wc, douche, bad en lavabo", "Keukenafvoer en vetleidingen", "Hoofdriolering binnen en buiten de woning", "Water dat terugkomt via vloerputjes of kelderafvoeren", "Rioolgeur, borrelende geluiden en terugslagproblemen"],
    },
    {
      title: "Aanpak",
      bullets: ["Korte bevraging van het probleem", "Inspectie van de betrokken afvoeren", "Mechanische ontstopping met professionele apparatuur", "Indien nodig: camera-inspectie voor diagnose", "Controle en advies om herhaling te vermijden"],
    },
    {
      title: "Prijzen",
      body: "Wij werken met vaste en transparante prijzen, ook ’s avonds en in het weekend:",
      bullets: ["Interventie ontstopping: €160", "Camera-inspectie: €90", "Totaalpakket (ontstopping + camera): €250"],
    },
    {
      title: "Waarom snel reageren?",
      body: "Hoe sneller je ingrijpt, hoe kleiner de kans op bijkomende schade zoals geurhinder, overstroming of lekkages. Een korte interventie voorkomt vaak duurdere herstellingen.",
    },
  ],
  ctaTitle: "Hulp nodig bij een verstopping?",
  ctaBody: "Beschrijf kort het probleem en voeg indien mogelijk een foto toe. Wij koppelen snel terug met een concreet tijdsblok in Antwerpen Stad.",
  ctaButton: "Vraag ontstopping aan →",
  serviceKey: "ontstoppingen",
  heroImageKey: "ontstoppingen-antwerpen-stad",
};

export default function Page() {
  return <DienstPageLayout {...pageProps} />;
}
