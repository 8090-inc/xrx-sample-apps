import React from "react";
import styles from "./PreInteractionComponent.module.css";
import { WidgetWrapper, ScrollableList, ItemCard } from "../base/Base";

interface PopularDish {
  name: string;
  image: string;
}

const PopularDish: React.FC<PopularDish> = ({ name, image }) => {
  return (
    <div className={styles.itemContainer}>
      <div className={styles.itemImageContainer}>
        <img src={image} alt={name} width={100} height={100} />
      </div>
      <div className={styles.itemName}>{name}</div>
    </div>
  );
};

const popularDishes = [
  {
    name: "Brooklyn Style Pizza",
    image:
      "https://cdn.shopify.com/s/files/1/0706/8473/7786/files/dominospizza.jpg?v=1722871676"
  },
  {
    name: "Chicken Wings",
    image:
      "https://cdn.shopify.com/s/files/1/0706/8473/7786/files/chickenwings.jpg?v=1722871573"
  }
];

const PreInteractionComponent: React.FC<{ agentType: string }> = ({
  agentType
}) => {
  return agentType === "pizza-agent" ? (
    <WidgetWrapper title="Popular Items">
      {popularDishes.map((dish) => (
        <ItemCard key={dish.name} title={dish.name} image={dish.image} />
      ))}
    </WidgetWrapper>
  ) : null;
};

export default PreInteractionComponent;
