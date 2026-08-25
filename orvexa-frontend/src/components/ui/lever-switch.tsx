import * as React from "react";
import { cn } from "@/lib/utils";
import "./lever-switch.css";

export interface LeverSwitchProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  checked?: boolean;
  defaultChecked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  label?: string;
  sublabel?: string;
}

export const LeverSwitch = React.forwardRef<HTMLInputElement, LeverSwitchProps>(
  (
    {
      className,
      checked: controlledChecked,
      defaultChecked = false,
      onCheckedChange,
      onChange,
      disabled,
      label,
      sublabel,
      ...props
    },
    ref
  ) => {
    const [uncontrolledChecked, setUncontrolledChecked] =
      React.useState(defaultChecked);
    const isControlled = controlledChecked !== undefined;
    const isChecked = isControlled ? controlledChecked : uncontrolledChecked;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      if (disabled) return;
      if (!isControlled) {
        setUncontrolledChecked(e.target.checked);
      }
      onChange?.(e);
      onCheckedChange?.(e.target.checked);
    };

    return (
      <label
        className={cn(
          "inline-flex items-center gap-3 cursor-pointer select-none",
          disabled && "opacity-50 cursor-not-allowed",
          className
        )}
      >
        <div
          className={cn(
            "lever-toggle-container",
            disabled && "disabled"
          )}
        >
          <input
            ref={ref}
            type="checkbox"
            className="lever-toggle-input"
            checked={isChecked}
            onChange={handleChange}
            disabled={disabled}
            {...props}
          />
          <div className="lever-toggle-handle-wrapper">
            <div className="lever-toggle-handle">
              <div className="lever-toggle-handle-knob" />
              <div className="lever-toggle-handle-bar-wrapper">
                <div className="lever-toggle-handle-bar" />
              </div>
            </div>
          </div>
          <div className="lever-toggle-base">
            <div className="lever-toggle-base-inside" />
          </div>
        </div>

        {(label || sublabel) && (
          <div className="flex flex-col">
            {label && (
              <span className="text-xs font-mono font-bold text-slate-200">
                {label}
              </span>
            )}
            {sublabel && (
              <span className="text-[10px] font-mono text-slate-500">
                {sublabel}
              </span>
            )}
          </div>
        )}
      </label>
    );
  }
);

LeverSwitch.displayName = "LeverSwitch";

// Alias exported as Component for exact drop-in snippet compatibility
export const Component = LeverSwitch;
export default LeverSwitch;
