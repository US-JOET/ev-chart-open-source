/**
 * Custom Link component for EV-ChART tooltip components.
 * @packageDocumentation
 **/
import React from "react";

/**
 * Custom link code for the tooltips
 */
export type CustomLinkProps = React.PropsWithChildren<{
  className?: string;
}> &
  JSX.IntrinsicElements["a"] &
  React.RefAttributes<HTMLAnchorElement>;

const CustomLink = React.forwardRef<HTMLAnchorElement, CustomLinkProps>(function CustomLink(
  { ...props }: CustomLinkProps,
  ref,
) {
  return <a ref={ref} {...props} />;
});

export default CustomLink;
