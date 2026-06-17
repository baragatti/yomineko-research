/** Material Symbols Rounded icon (font loaded in root). Standalone, no app-store coupling. */
export function Icon({
  name,
  size = 24,
  fill = false,
  weight = 400,
  color,
  className,
  style,
}: {
  name: string;
  size?: number;
  fill?: boolean;
  weight?: number;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <span
      className={`material-symbols-rounded${className ? " " + className : ""}`}
      style={{
        fontSize: size,
        lineHeight: 1,
        color,
        fontVariationSettings: `'FILL' ${fill ? 1 : 0}, 'wght' ${weight}, 'GRAD' 0, 'opsz' ${size}`,
        userSelect: "none",
        ...style,
      }}
    >
      {name}
    </span>
  );
}
