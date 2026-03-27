interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export function PageHeader({ title, subtitle, action }: PageHeaderProps) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4 md:mb-8">
      <div>
        <p className="mb-2 font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
          Meal.OS
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1 text-sm text-muted-foreground md:text-base">
            {subtitle}
          </p>
        )}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}
