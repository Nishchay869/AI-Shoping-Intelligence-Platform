// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ProductCard } from "@/components/ui";
import type { Product } from "@/lib/mock-data";

const product: Product = {
  id: "test-product",
  title: "Test Wireless Headphones",
  brand: "TestBrand",
  image: "https://images.unsplash.com/photo-test",
  category: "Audio",
  currentPrice: 24990,
  previousPrice: 29990,
  currency: "₹",
  rating: 4.8,
  reviews: 2841,
  retailer: "Amazon",
  trend: "down",
};

describe("ProductCard", () => {
  it("renders the product title, brand, retailer, price, and rating", () => {
    render(<ProductCard product={product} />);
    expect(screen.getByText("Test Wireless Headphones")).toBeInTheDocument();
    expect(screen.getByText(/TestBrand/)).toBeInTheDocument();
    expect(screen.getByText(/Amazon/)).toBeInTheDocument();
    expect(screen.getByText(/24,990/)).toBeInTheDocument();
    expect(screen.getByText(/4.8/)).toBeInTheDocument();
  });

  it("computes and displays the discount percentage when price dropped", () => {
    render(<ProductCard product={product} />);
    // (1 - 24990/29990) * 100 = 16.67%, rounded to 17%
    expect(screen.getByText("↓ 17%")).toBeInTheDocument();
  });

  it("does not display a discount badge when there is no price drop", () => {
    render(<ProductCard product={{ ...product, currentPrice: 27900, previousPrice: 27900 }} />);
    expect(screen.queryByText(/↓/)).not.toBeInTheDocument();
  });

  it("links to the product detail page", () => {
    render(<ProductCard product={product} />);
    expect(screen.getByRole("link", { name: "Test Wireless Headphones" })).toHaveAttribute("href", "/products/test-product");
  });

  it("defaults the wishlist toggle to not-saved and toggles on click", async () => {
    const user = userEvent.setup();
    render(<ProductCard product={product} />);
    const toggle = screen.getByRole("button", { name: "Add to wishlist" });
    expect(toggle).toBeInTheDocument();

    await user.click(toggle);
    expect(screen.getByRole("button", { name: "Remove from wishlist" })).toBeInTheDocument();
  });

  it("respects an initial saved=true prop", () => {
    render(<ProductCard product={product} saved />);
    expect(screen.getByRole("button", { name: "Remove from wishlist" })).toBeInTheDocument();
  });
});
