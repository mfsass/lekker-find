import React from "react";
import { cn } from "../../lib/utils";

type RainbowButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement>;

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
