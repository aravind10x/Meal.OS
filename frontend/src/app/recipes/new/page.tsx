"use client";

import { useRouter } from "next/navigation";
import { NavBar } from "@/components/common/nav-bar";
import { PageHeader } from "@/components/common/page-header";
import { RecipeForm } from "@/components/recipe/recipe-form";
import { api } from "@/lib/api";
import type { RecipeCreate } from "@/types";
import { toast } from "sonner";

export default function NewRecipePage() {
  const router = useRouter();

  const handleSubmit = async (data: RecipeCreate) => {
    try {
      await api.recipes.create(data);
      toast.success(`Recipe "${data.name}" created!`);
      router.push(`/recipes/${data.id}`);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to create recipe";
      toast.error(message);
      throw err; // re-throw so the form knows it failed
    }
  };

  return (
    <div className="min-h-screen pb-20">
      <div className="mx-auto max-w-lg px-4 pt-6">
        <PageHeader title="Add Recipe" subtitle="Create a new house-style recipe" />
        <RecipeForm
          isNew
          onSubmit={handleSubmit}
          onCancel={() => router.push("/recipes")}
          submitLabel="Create Recipe"
        />
      </div>
      <NavBar />
    </div>
  );
}
