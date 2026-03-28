"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { NavBar } from "@/components/common/nav-bar";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { toast } from "sonner";
import {
  ArrowLeft,
  ChefHat,
  Loader2,
  ShoppingCart,
  Copy,
  Check,
  Mic,
  Play,
  Pause,
  Download,
  Share2,
  ChevronDown,
  ChevronUp,
  Volume2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { VoiceAudioResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function parseBriefText(brief: string): {
  title: string;
  sections: Array<{ title: string; items: string[] }>;
} {
  const lines = brief
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .filter((line) => !/^━+$/.test(line));

  let title = "";
  const sections: Array<{ title: string; items: string[] }> = [];
  let currentSection: { title: string; items: string[] } | null = null;

  lines.forEach((line, index) => {
    if (index === 0 && line.includes("COOK BRIEF")) {
      title = line;
      return;
    }

    if (!line.startsWith("•")) {
      currentSection = {
        title: line.replace(/^[^A-Za-z0-9']+\s*/, ""),
        items: [],
      };
      sections.push(currentSection);
      return;
    }

    currentSection?.items.push(line.replace(/^•\s*/, ""));
  });

  return { title, sections };
}

export default function CookBriefPage() {
  const params = useParams();
  const router = useRouter();
  const rawId = params.id;
  const planId = typeof rawId === "string" ? Number(rawId) : NaN;

  // Brief state
  const [brief, setBrief] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Voice state
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [voiceData, setVoiceData] = useState<VoiceAudioResponse | null>(null);
  const [scriptExpanded, setScriptExpanded] = useState(false);

  // Audio player state
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Load cook brief (includes cached voice data if it exists)
  useEffect(() => {
    if (isNaN(planId)) {
      setError("Invalid plan ID");
      setLoading(false);
      return;
    }
    api.brief
      .get(planId)
      .then((data) => {
        setBrief(data.brief_text);
        // Restore previously generated voice data from the brief response
        if (data.voice_audio_url) {
          setVoiceData({
            plan_id: data.plan_id,
            audio_url: data.voice_audio_url,
            script_text: data.voice_script_text ?? "",
          });
        }
      })
      .catch(() => toast.error("Failed to load cook brief"))
      .finally(() => setLoading(false));
  }, [planId]);

  // Generate voice note — calls only getAudio (which generates script internally if needed)
  const handleGenerateVoice = useCallback(async () => {
    if (isNaN(planId)) return;
    setVoiceLoading(true);
    try {
      const audioData = await api.voice.getAudio(planId);
      setVoiceData(audioData);

      if (audioData.audio_url) {
        toast.success("Voice note generated!");
      } else if (audioData.tts_error) {
        toast.error(audioData.tts_error);
        // Still show the script for manual recording
        setScriptExpanded(true);
      }
    } catch {
      toast.error("Failed to generate voice note");
    } finally {
      setVoiceLoading(false);
    }
  }, [planId]);

  // Audio controls
  const togglePlayPause = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  // Handle audio ended
  const handleAudioEnded = useCallback(() => {
    setIsPlaying(false);
  }, []);

  // Download audio
  const handleDownload = useCallback(async () => {
    if (!voiceData?.audio_url) return;
    try {
      const blob = await api.voice.downloadAudio(voiceData.audio_url);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cook_brief_${planId}.mp3`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Audio downloaded!");
    } catch {
      toast.error("Failed to download audio");
    }
  }, [voiceData, planId]);

  // Share to WhatsApp
  const handleShare = useCallback(async () => {
    if (!voiceData?.audio_url) return;

    try {
      const blob = await api.voice.downloadAudio(voiceData.audio_url);
      const file = new File([blob], `cook_brief_${planId}.mp3`, {
        type: "audio/mpeg",
      });

      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({
          title: "Cook Brief - Voice Note",
          text: "Tomorrow's cooking instructions",
          files: [file],
        });
        toast.success("Shared successfully!");
      } else {
        // Fallback: copy script text
        await navigator.clipboard.writeText(voiceData.script_text);
        toast.success(
          "Share not supported — Hindi script copied to clipboard instead"
        );
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        toast.error("Failed to share");
      }
    }
  }, [voiceData, planId]);

  // Copy brief
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(brief);
      setCopied(true);
      toast.success("Brief copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy");
    }
  };

  const parsedBrief = parseBriefText(brief);

  if (error) {
    return (
      <div className="min-h-screen pb-20">
        <div className="mx-auto max-w-4xl px-4 pt-6 md:px-6 lg:px-8">
          <PageHeader title="Cook Brief" subtitle="Error" />
          <Card className="p-6 text-center">
            <p className="text-sm text-red-600">{error}</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => router.back()}
            >
              Go Back
            </Button>
          </Card>
        </div>
        <NavBar />
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-20">
      <div className="mx-auto max-w-4xl px-4 pt-6 md:px-6 lg:px-8 xl:max-w-5xl">
        <PageHeader
          title="Cook Brief"
          subtitle="Share-ready handoff"
          action={
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
          }
        />

        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
          </div>
        ) : (
          <>
            <Card className="mb-4 rounded-[1.8rem] border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(244,244,239,0.72))] p-5 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
                    Brief artifact
                  </p>
                  <h2 className="mt-2 text-xl font-semibold tracking-tight text-zinc-900">
                    {parsedBrief.title || "Cook brief ready"}
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-zinc-600">
                    Structured for the cook to execute without extra
                    back-and-forth.
                  </p>
                </div>
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-secondary text-primary">
                  <ChefHat className="h-5 w-5" />
                </div>
              </div>

              {parsedBrief.sections.length > 0 ? (
                <div className="mt-5 grid gap-3">
                  {parsedBrief.sections.map((section) => (
                    <div
                      key={section.title}
                      className="rounded-[1.4rem] border border-white/80 bg-white/76 p-4"
                    >
                      <p className="font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
                        {section.title}
                      </p>
                      <div className="mt-3 space-y-2">
                        {section.items.map((item) => (
                          <p
                            key={item}
                            className="text-sm leading-6 text-zinc-700"
                          >
                            • {item}
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <pre className="mt-5 overflow-x-auto rounded-[1.4rem] bg-zinc-50 p-4 font-mono text-sm leading-relaxed text-zinc-700 whitespace-pre-wrap">
                  {brief}
                </pre>
              )}
            </Card>

            <Card className="mb-4 rounded-[1.8rem] border-white/70 p-5">
                <div className="mb-3 flex items-center gap-2">
                  <Volume2 className="h-5 w-5 text-emerald-600" />
                  <div>
                    <h2 className="font-semibold text-zinc-900">
                      Hindi Voice Note
                    </h2>
                    <p className="text-sm text-zinc-500">
                      Structured for WhatsApp or voice
                    </p>
                  </div>
                </div>

                {!voiceData && !voiceLoading && (
                  <Button
                    className="w-full gap-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700"
                    onClick={handleGenerateVoice}
                  >
                    <Mic className="h-4 w-4" />
                    Generate Voice Note
                  </Button>
                )}

                {voiceLoading && (
                  <div className="flex items-center justify-center gap-3 py-6">
                    <Loader2 className="h-5 w-5 animate-spin text-emerald-500" />
                    <span className="text-sm text-zinc-500">
                      Generating Hindi voice note...
                    </span>
                  </div>
                )}

                {voiceData && (
                  <div className="space-y-3">
                    {voiceData.audio_url && (
                      <>
                        <audio
                          ref={audioRef}
                          src={`${API_BASE}${voiceData.audio_url}`}
                          onEnded={handleAudioEnded}
                          preload="auto"
                        />
                        <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-3">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-10 w-10 shrink-0 rounded-full bg-emerald-600 text-white hover:bg-emerald-700"
                            onClick={togglePlayPause}
                          >
                            {isPlaying ? (
                              <Pause className="h-5 w-5" />
                            ) : (
                              <Play className="ml-0.5 h-5 w-5" />
                            )}
                          </Button>
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium text-emerald-800">
                              Cook Brief Voice Note
                            </p>
                            <p className="text-xs text-emerald-600">
                              Hindi • Listen before sending
                            </p>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <Button
                            variant="outline"
                            className="gap-2 rounded-xl"
                            onClick={handleDownload}
                          >
                            <Download className="h-4 w-4" />
                            Download
                          </Button>
                          <Button
                            className="gap-2 rounded-xl bg-green-600 text-white hover:bg-green-700"
                            onClick={handleShare}
                          >
                            <Share2 className="h-4 w-4" />
                            Share WhatsApp
                          </Button>
                        </div>
                      </>
                    )}

                    {voiceData.tts_error && !voiceData.audio_url && (
                      <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
                        ⚠️ {voiceData.tts_error}
                      </div>
                    )}

                    <button
                      type="button"
                      className="flex items-center gap-1 text-sm text-zinc-500 transition-colors hover:text-zinc-700"
                      onClick={() => setScriptExpanded(!scriptExpanded)}
                    >
                      {scriptExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                      {scriptExpanded
                        ? "Hide Hindi script"
                        : "Show Hindi script (for manual recording)"}
                    </button>

                    {scriptExpanded && voiceData.script_text && (
                      <div className="rounded-lg bg-zinc-50 p-4">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap text-zinc-700">
                          {voiceData.script_text}
                        </p>
                      </div>
                    )}
                  </div>
                )}
            </Card>

            <div className="space-y-3">
              <Button
                variant="outline"
                className="w-full gap-2 rounded-xl"
                onClick={handleCopy}
              >
                {copied ? (
                  <Check className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
                {copied ? "Copied!" : "Copy Brief"}
              </Button>
              <Button
                variant="outline"
                className="w-full gap-2 rounded-xl"
                onClick={() => router.push(`/shopping/${planId}`)}
              >
                <ShoppingCart className="h-4 w-4" />
                View Shopping List
              </Button>
            </div>
          </>
        )}
      </div>
      <NavBar />
    </div>
  );
}
