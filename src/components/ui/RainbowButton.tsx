import React from "react";
import { cn } from "../../lib/utils";

interface RainbowButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement> { }

export function RainbowButton({
    children,
    className,
    ...props
}: RainbowButtonProps) {
    return (
        <button
            className={cn(
                "btn-rainbow group",
                className
            )}
            {...props}
        >
            <span className="btn-rainbow-content">
                {children}
            </span>
        </button>
    );
}
