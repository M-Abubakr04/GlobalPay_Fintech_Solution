import { Link } from "react-router-dom";

export function NotFoundPage() {
  return <div className="not-found"><strong>404</strong><h2>Page not found</h2><p>The requested GlobalPay workspace does not exist.</p><Link className="primary-button" to="/">Return to overview</Link></div>;
}
