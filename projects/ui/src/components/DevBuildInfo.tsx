type DevBuildInfoProps = {
  buildDatetime: string;
  buildHash: string;
  className?: string;
};

export default function DevBuildInfo({
  buildDatetime,
  buildHash,
  className,
}: DevBuildInfoProps): JSX.Element {
  return (
    <div
      className={
        className ??
        "text-xs p-2 bg-black/60 text-white rounded md:self-end max-w-full break-all"
      }
      style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" }}
    >
      <div>buildDatetime: {buildDatetime}</div>
      <div>buildHash: {buildHash}</div>
    </div>
  );
}
